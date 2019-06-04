from django.db.models import F, Value
from django_filters import CharFilter
from django_filters.rest_framework import BaseInFilter, NumberFilter
from tipsi_tools.django.db.pgfields import WordSimilarity
from tipsi_tools.django.db.utils import set_word_similarity_threshold


class NumberInFilter(BaseInFilter, NumberFilter):
    pass


class TrigramFilter(CharFilter):
    def __init__(self, *args, **kwargs):
        self.similarity_threshold = kwargs.pop('similarity_threshold', None)
        super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        if value:
            if self.similarity_threshold:
                set_word_similarity_threshold(1 - self.similarity_threshold)
            similarity = WordSimilarity(Value(value), F(self.field_name))
            qs = (
                qs.annotate(similarity=similarity)
                .order_by('similarity', 'pk')
                .filter(**{f'{self.field_name}__similar': value})
            )
        return qs
