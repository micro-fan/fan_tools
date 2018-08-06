from enum import Enum

from rest_framework import fields


class EnumSerializer(fields.Field):
    default_error_messages = {'invalid': '{value!r} not valid value for: {values}'}

    def __init__(self, enum, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enum = enum

    def to_internal_value(self, data):
        if data is None:
            return None
        try:
            return getattr(self.enum, data)
        except TypeError:
            try:
                return self.enum(data)
            except ValueError:
                values = [x.name for x in self.enum]
                self.fail('invalid', value=data, values=values)
        except AttributeError:
            values = [x.name for x in self.enum]
            self.fail('invalid', value=data, values=values)

    def to_representation(self, value):
        if isinstance(value, Enum):
            return value.name
        return self.enum(value).name
