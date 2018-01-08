from rest_framework import fields
from rest_framework.serializers import ListSerializer
from rest_framework_dyn_serializer import DynModelSerializer

primitive_types = {
    fields.IntegerField: 'int',
    fields.BooleanField: 'bool',
    fields.FloatField: 'float',
    fields.CharField: 'str',
    fields.ImageField: 'http-link',
    fields.DateTimeField: 'datetime',
    fields.DateField: 'date',
    fields.JSONField: 'json/object',
}


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
        ]
    }


def process_fields(name, field, serializer):
    cls = field.__class__

    result = {
        'name': name,
        'readonly': bool(field.read_only),
        'write_only': bool(field.write_only),
        'required': bool(field.required),
        'allow_null': bool(field.allow_null),
        'is_dyn_serializer': issubclass(cls, DynModelSerializer),
        '__field__': repr(field),
        '__class__': repr(cls),
    }

    _type = {}

    if cls in primitive_types:
        _type['primitive_type'] = primitive_types[cls]
    elif cls == fields.SerializerMethodField:
        method_name = field.method_name or 'get_{}'.format(name)
        method = getattr(serializer, method_name)
        _type['method_type'] = {
            'method_name': method_name,
            'method_doc': method.__doc__ if method and method.__doc__ else None,
        }
    elif issubclass(cls, DynModelSerializer):
        _type['dyn_field_type'] = {
            'ref_name': cls.__name__,
        }
    elif (issubclass(cls, ListSerializer) and
          isinstance(field.child, DynModelSerializer)):
        _type['list_field_type'] = {
            'ref_name': field.child.__class__.__name__,
        }
    else:
        model_doc = None
        if hasattr(serializer, 'Meta') and hasattr(serializer.Meta, 'model'):
            # parse docstring in custom model methods
            fun = getattr(serializer.Meta.model, name, {})
            model_doc = fun.__doc__

        serializer_doc = field.__doc__
        if model_doc or serializer_doc:
            _type['doc_type'] = {
                'model_doc': model_doc,
                'serializer_doc': serializer_doc,
            }

    result['type'] = _type
    print('Process: <SerializerField: {}/>'.format(name))
    return result
