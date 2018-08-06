from django.db.models import CharField, Field, Func, Lookup


class LTreeField(CharField):
    description = 'pg ltree (up to %(max_length)s)'

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 256
        super().__init__(*args, **kwargs)

    def db_type(self, connection):
        return 'ltree'

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs['max_length']
        return name, path, args, kwargs


class LTreeDescendant(Lookup):
    lookup_name = 'descendant'

    def as_sql(self, qn, connection):
        lhs, lhs_params = self.process_lhs(qn, connection)
        rhs, rhs_params = self.process_rhs(qn, connection)
        params = lhs_params + rhs_params
        return '%s <@ %s' % (lhs, rhs), params


LTreeField.register_lookup(LTreeDescendant)


class SimilarityLookup(Lookup):
    lookup_name = 'similar'

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        res = '{} %%> {}'.format(lhs, rhs), params
        return res


Field.register_lookup(SimilarityLookup)


class WordSimilarity(Func):
    template = '%(expressions)s'
    arg_joiner = '<<->'
