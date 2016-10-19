import django_filters
from functools import reduce

import logging

from django.db.models import Q


class EnumFilter(django_filters.CharFilter):
    def __init__(self, enum, *args, **kwargs):
        self._enum = enum
        super().__init__(*args, **kwargs)

    def filter(self, qs, name):
        try:
            q_objects = []
            names = name.split(',')
            for n in names:
                if n:
                    value = getattr(self._enum, n)
                    q = Q(**{'{}__exact'.format(self.name): value})
                    q_objects.append(q)

            if q_objects:
                return qs.filter(reduce(lambda q1, q2: q1 | q2, q_objects))
            else:
                return qs

        except Exception:
            logging.exception('Failed to convert value')
            return super(EnumFilter, self).filter(qs, None)
