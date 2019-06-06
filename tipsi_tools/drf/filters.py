import logging
from functools import reduce

import django_filters
from django.db.models import Q, F, Value
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


class EnumFilter(django_filters.CharFilter):
    def __init__(self, enum, *args, **kwargs):
        self._enum = enum
        super().__init__(*args, **kwargs)

    def filter(self, qs, name):
        # In django filters 2.0 `name` is renamed to `field_name`
        self_name = getattr(self, 'name', None) or getattr(self, 'field_name')
        try:
            q_objects = []
            if isinstance(name, str):
                names = name.split(',')
                for n in names:
                    if hasattr(self._enum, n):
                        value = getattr(self._enum, n)
                        q = Q(**{'{}__exact'.format(self_name): value})
                        q_objects.append(q)
                    elif n == 'null':
                        q_objects.append(Q(**{'{}__isnull'.format(self_name): True}))
            elif name is None:
                q_objects.append(Q(**{'{}__isnull'.format(self_name): True}))
            else:
                raise AttributeError
            if q_objects:
                return self.get_method(qs)(reduce(lambda q1, q2: q1 | q2, q_objects))
            else:
                return qs

        except Exception:
            logging.exception('Failed to convert value: {} {}'.format(self_name, name))
            return super(EnumFilter, self).filter(qs, None)
