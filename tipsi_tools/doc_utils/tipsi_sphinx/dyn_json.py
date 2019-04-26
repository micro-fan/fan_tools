import sys
from contextlib import suppress

from tipsi_tools.drf.serializers import EnumSerializer

from django.core.exceptions import ImproperlyConfigured
from django.core.validators import RegexValidator
from django.db.models import AutoField, ForeignKey, OneToOneField
from rest_framework import fields
from rest_framework.fields import ListField
from rest_framework.serializers import ListSerializer
from rest_framework_dyn_serializer import DynModelSerializer

try:
    from django.contrib.gis.db.models import MultiPointField
except ImproperlyConfigured as e:
    print(
        f'WARNING: Can not import MultiPointField. Fields with this type will be skipped. ({e})',
        file=sys.stderr,
    )
    MultiPointField = type(None)


def fields_regexp(field):
    pattern = '*'
    for validator in field.validators:
        if isinstance(validator, RegexValidator):
            pattern = validator.regex.pattern

    return f'str regex({pattern})'


def fields_enum(field):
    values = ', '.join(v.name for v in field.enum)
    return f'str enum({values})'


def fields_choices(field):
    # TODO: choices type - str vs int
    values = ', '.join(str(name) for name in field.choices)
    return f'str enum({values})'


def fields_model(field):
    return django_types.get(field.model_field.__class__)


django_types = {MultiPointField: 'list[(x:float, y:float), ..]'}


primitive_types = {
    fields.IntegerField: 'int',
    fields.BooleanField: 'bool',
    fields.FloatField: 'float',
    fields.CharField: 'str',
    fields.ImageField: 'http-link',
    fields.DateTimeField: 'datetime',
    fields.DateField: 'date',
    fields.JSONField: 'json/object',
    fields.URLField: 'http-link',
    fields.RegexField: fields_regexp,
    fields.EmailField: 'email',
    fields.ChoiceField: fields_choices,
    fields.DecimalField: 'decimal',
    fields.ModelField: fields_model,
    EnumSerializer: fields_enum,
}


def primitive_type(cls, field):
    for field_class, field_type in primitive_types.items():
        if issubclass(cls, field_class):
            return {'primitive_type': field_type(field) if callable(field_type) else field_type}

    return None


def serializer_doc_info(serializer, path_info=''):
    print('Run: {}'.format(path_info))

    if not hasattr(serializer, 'Meta'):
        serializer.Meta = type("Meta", tuple(), {})
    if not hasattr(serializer.Meta, 'fields_param'):
        serializer.Meta.fields_param = 'any'

    serializer_obj = serializer()

    return {
        'class_name': serializer.__name__,
        'class_module': serializer.__module__,
        'field_param': serializer.Meta.fields_param,
        'fields': [
            process_fields(name, field, serializer_obj)
            for name, field in sorted(serializer_obj.fields.items())
        ],
        'class_doc': serializer.__doc__,
    }


def process_fields(name, field, serializer):
    cls = field.__class__

    model = None
    model_field = None
    if hasattr(serializer, 'Meta') and hasattr(serializer.Meta, 'model'):
        model = serializer.Meta.model
        with suppress(Exception):
            model_field = model._meta.get_field(name)

    # ManyToOneRel and ManyToManyRel don't have help_text
    help_text = field.help_text or getattr(model_field, 'help_text', None)

    result = {
        'name': name,
        'readonly': bool(field.read_only),
        'write_only': bool(field.write_only),
        'required': bool(field.required),
        'allow_null': bool(field.allow_null),
        'is_dyn_serializer': issubclass(cls, DynModelSerializer),
        'help_text': help_text,
        '__field__': repr(field),
        '__class__': repr(cls),
        'type': get_type(field, serializer, model_field, model, name),
    }

    print('Process: <SerializerField: {}/>'.format(name))
    return result


def get_type(field, serializer, model_field, model, name):
    cls = field.__class__

    p_type = primitive_type(cls, field)
    if p_type:
        return p_type

    if cls == fields.SerializerMethodField:
        method_name = field.method_name or 'get_{}'.format(name)
        method = getattr(serializer, method_name)
        return {
            'method_type': {
                'method_name': method_name,
                'method_doc': method.__doc__ if method and method.__doc__ else None,
            }
        }

    if issubclass(cls, DynModelSerializer):
        return {'dyn_field_type': {'ref_name': cls.__name__}}

    if issubclass(cls, ListSerializer) and isinstance(field.child, DynModelSerializer):
        return {'list_field_type': {'ref_name': field.child.__class__.__name__}}

    if issubclass(cls, ListField):
        p_type = primitive_type(field.child.__class__, field.child)
        if p_type:
            return {'list_field_type': p_type}

    if model_field is not None and isinstance(model_field, ForeignKey):
        # if issubclass(model_field, ForeignKey):
        related_field = model_field.target_field
        while isinstance(related_field, OneToOneField):  # Table inheritance
            related_field = related_field.target_field
        related_types = {AutoField: 'int (related)'}
        if related_field.__class__ in related_types:
            return {'primitive_type': related_types[related_field.__class__]}

    model_doc = None
    if model is not None:
        # parse docstring in custom model methods
        fun = getattr(model, name, {})
        model_doc = fun.__doc__

    serializer_doc = field.__doc__
    if model_doc or serializer_doc:
        return {'doc_type': {'model_doc': model_doc, 'serializer_doc': serializer_doc}}

    return {}
