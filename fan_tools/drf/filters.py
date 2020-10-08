import logging
from functools import reduce

import django_filters
from django.db.models import F, Q, Value
from django_filters import CharFilter
from django_filters.rest_framework import BaseInFilter, NumberFilter
from rest_framework.exceptions import ValidationError

from fan_tools.django.db.pgfields import WordSimilarity
from fan_tools.django.db.utils import set_word_similarity_threshold


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
    def __init__(self, enum, *args, raise_on_error=False, **kwargs):
        self._enum = enum
        self.raise_on_error = raise_on_error
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
                    elif n and self.raise_on_error:
                        raise ValidationError(
                            {self_name: f'Invalid choice={n!r} Valid: {list(self._enum.__members__.keys())}'}
                        )
            elif name is None:
                q_objects.append(Q(**{'{}__isnull'.format(self_name): True}))
            else:
                raise AttributeError
            if q_objects:
                return self.get_method(qs)(reduce(lambda q1, q2: q1 | q2, q_objects))
            else:
                return qs
        except ValidationError:
            raise
        except Exception:
            logging.exception('Failed to convert value: {} {}'.format(self_name, name))
            return super(EnumFilter, self).filter(qs, None)
