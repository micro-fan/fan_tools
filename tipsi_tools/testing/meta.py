class PropsMeta(type):
    '''
    Replace all methods prop_[METHODNAME] with property
    This property return method result and cache it between calls
    Cached result stored in __[METHODNAME]
    '''
    def __new__(cls, name, bases, attrs, **kwargs):
        new_attrs = cls.new_attrs(attrs)
        return type.__new__(cls, name, bases, new_attrs)

    PROP = 'prop__'

    @classmethod
    def new_attrs(cls, attrs):
        new_attrs = {}

        def is_empty(self, name):
            return not hasattr(self, name)

        for name, value in list(attrs.items()):
            if not name.startswith(cls.PROP):
                new_attrs[name] = value
                continue
            new_name = name.replace(cls.PROP, '')
            attr_name = '__{}'.format(new_name)

            def _prop_wrapper(value_func, attr_name):
                def wrapped(self):
                    if is_empty(self, attr_name):
                        setattr(self, attr_name, value_func(self))
                    return getattr(self, attr_name)
                return wrapped

            new_attrs[new_name] = property(_prop_wrapper(value, attr_name))
        return new_attrs
