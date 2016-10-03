# About this package

[![Build Status](https://travis-ci.org/tipsi/tipsi_tools.svg?branch=master)](https://travis-ci.org/tipsi/tipsi_tools)

Here are set of internal tools that are shared between different projects internally. Originally most tools related to testing, so they provide some base classes for various cases in testing

**NOTE: all our tools are intentially support only 3.5+ python.**
Some might work with other versions, but we're going to be free from all these crutches to backport things like `async/await` to lower versions, so if it works - fine, if not - feel free to send PR, but it isn't going to be merged all times.


## PropsMeta

You can find source in `tipsi_tools/testing/meta.py`.

For now it convert methods that are started with `prop__` into descriptors with cache.

```python
class A(metaclass=PropsMeta):
    def prop__conn(self):
        conn = SomeConnection()
        return conn
```

Became:

```python
class A:
    @property
    def conn(self):
        if not hasattr(self, '__conn'):
            setattr(self, '__conn', SomeConnection())
        return self.__conn
```

Thus it allows quite nice style of testing with lazy initialization. Like:

```python
class MyTest(TestCase, metaclass=PropsMeta):
    def prop__conn(self):
        return psycopg2.connect('')

    def prop__cursor(self):
        return self.conn.cursor()

    def test_simple_query(self):
        self.cursor.execute('select 1;')
        row = self.cursor.fetchone()
        assert row[0] == 1, 'Row: {}'.format(row)

```

Here you just get and use `self.cursor`, but automatically you get connection and cursor and cache they.

This is just simple example, complex tests can use more deep relations in tests. And this approach is way more easier and faster than complex `setUp` methods.


## AIOTestCase

Base for asyncronous test cases, you can use it as drop-in replacement for pre-existent tests to be able:

* write asyncronous test methods
* write asyncronous `setUp` and `tearDown` methods
* use asyncronous function in `assertRaises`

```python
class ExampleCase(AIOTestCase):
    async setUp(self):
        await async_setup()

    async tearDown(self):
        await async_teardown()

    async division(self):
        1/0

    async test_example(self):
        await self.assertRaises(ZeroDivisionError, self.async_division)
```

## Commands

### tipsi_env_yaml

Convert template yaml with substituion of `%{ENV_NAME}` strings to appropriate environment variables.

Usage: `tipsi_env_yaml src_file dst_file`
