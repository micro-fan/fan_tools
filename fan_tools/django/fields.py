import enum


class ChoicesEnum(enum.IntEnum):
    @classmethod
    def get_choices(cls):
        return [(x.value, x.name) for x in cls]
