import django_filters

from tipsi_tools import logging


class EnumFilter(django_filters.CharFilter):
    def filter(self, qs, name):
        try:
            q_objects = []
            names = name.split(',')
            for n in names:
                if n:
                    
                    q_objects.append(Q(status=status))
            if q_objects:
                return qs.filter(reduce(lambda q1, q2: q1 | q2, q_objects))
            else:
                return qs

        except Exception:
            logging.exception('Failed to convert value')
            return super(EnumFilter, self).filter(qs, None)
