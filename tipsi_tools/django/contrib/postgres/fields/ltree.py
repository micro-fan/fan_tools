from django.db.models import CharField, IntegerField, Lookup, Transform
from django.utils.translation import gettext_lazy as _
from django.core.validators import _lazy_re_compile, RegexValidator


class LTreeLabelField(CharField):
    description = _("PostgreSQL ltree label (up to %(max_length)s)")

    default_validators = [
        RegexValidator(
            _lazy_re_compile(r'^[a-zA-Z0-9_]+\Z'),
            _("Enter a valid 'ltree label' consisting of letters, numbers or underscores."),
            'invalid'
        )
    ]

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 255
        kwargs['editable'] = False
        kwargs['unique'] = True
        self.allow_unicode = False

        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()

        del kwargs['max_length']
        del kwargs['editable']
        del kwargs['unique']

        return name, path, args, kwargs


class LTreeLabelPathField(CharField):
    description = _("PostgreSQL ltree label path (up to %(max_length)s)")

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 2047
        kwargs['editable'] = False
        super().__init__(*args, **kwargs)

    def db_type(self, connection):
        return 'ltree'

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs['max_length']
        del kwargs['editable']
        return name, path, args, kwargs


class LTreeDescendants(Lookup):
    lookup_name = 'descendants'

    def as_sql(self, qn, connection):
        lhs, lhs_params = self.process_lhs(qn, connection)
        rhs, rhs_params = self.process_rhs(qn, connection)
        params = lhs_params + rhs_params
        return '%s <@ %s' % (lhs, rhs), params


class LTreeNlevel(Transform):
    lookup_name = 'nlevel'

    def as_sql(self, compiler, connection):
        lhs, params = compiler.compile(self.lhs)
        return 'nlevel(%s)' % lhs, params

    @property
    def output_field(self):
        return IntegerField()


LTreeLabelPathField.register_lookup(LTreeDescendants)
LTreeLabelPathField.register_lookup(LTreeNlevel)
