from django.db.models import Field, Func, Lookup


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
