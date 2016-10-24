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
            if isinstance(name, str):
                names = name.split(',')
                for n in names:
                    if hasattr(self._enum, n):
                        value = getattr(self._enum, n)
                        q = Q(**{'{}__exact'.format(self.name): value})
                        q_objects.append(q)
                    elif n == 'null':
                        q_objects.append(Q(**{'{}__isnull'.format(self.name): True}))
                    else:
                        raise AttributeError
            elif name is None:
                q_objects.append(Q(**{'{}__isnull'.format(self.name): True}))
            else:
                raise AttributeError
            if q_objects:
                return qs.filter(reduce(lambda q1, q2: q1 | q2, q_objects))
            else:
                return

        except Exception:
            logging.exception('Failed to convert value: {} {}'.format(self.name, name))
            return super(EnumFilter, self).filter(qs, None)
