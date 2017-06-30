class class_prop(object):
    """
    This decorator provide an easy to use interface to initialize and cache fixtures for test cases.
    With a little additional code for TestCase it can cache results of database operations for
    a whole test case.
    >>>@classmethod
    ...def setUpTestData(cls):
    ...    for name in dir(cls):
    ...        getattr(cls, name)

    Possible examples of usage:
    >>>class ExampleTestCase(TestCase):
    ...    @class_prop
    ...    def c(cls):
    ...        return cls.create_user('test_user')
    ...
    ...    c = class_prop(lambda cls: cls.create_user('user1'), name='c')
    Pay attention that decorated method behaves like a classmethod. Also if `class_prop` is used to
     decorate lambda function, it is necessary to provide additional keyword argument `name` with
     desired name for cached property.

    Also it can be used in test case mixins to provide collections of fixtures.
    >>>class TestUserMixing(object):
    ...    c1 = class_prop(lambda cls: cls.create_user('user1'), name='c1')
    ...    c2 = class_prop(lambda cls: cls.create_user('user2'), name='c2')
    """
    def __init__(self, f, name=None):
        self.f = f
        self.name = name

    def __get__(self, obj, klass=None):
        assert klass is not None, "Must not be used as an object attribute"

        result = self.f(klass)
        setattr(klass, self.name or self.f.__name__, result)
        return result
