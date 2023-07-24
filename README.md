# About this package


[![Build Status](https://img.shields.io/github/workflow/status/micro-fan/fan_tools/master)](https://github.com/micro-fan/fan_tools/actions)
[![PyPi version](https://img.shields.io/pypi/v/fan_tools.svg)](https://pypi.python.org/pypi/fan_tools)


Here are set of internal tools that are shared between different projects internally. Originally most tools related to testing, so they provide some base classes for various cases in testing

**NOTE: all our tools are intentially support only 3.8+ python.**
Some might work with other versions, but we're going to be free from all these crutches to backport things like `async/await` to lower versions, so if it works - fine, if not - feel free to send PR, but it isn't going to be merged all times.

## Testing helpers

### Caching decorators


```python
# cache async function that returns pydantic.BaseModel
from fan_tools.python import cache_async

@cache_async[type(dict)](fname, model, {})
async def func():
    return model


# cache sync function that returns json serializable response
from fan_tools.python import memoize

@memoize
def func(*args, **kwargs):
    return json.dumps(
        {
            'args': args,
            'kwargs': kwargs,
        }
    )
```

### ApiUrls

Defined in `fan_tools/testing/__init__.py`. Required for defining nested urls with formatting.

You can use it in fixtures, like:


```python
@pytest.fixture(scope='session')
def api(api_v_base):
    yield ApiUrls('{}/'.format(api_v_base), {
        'password_reset_request': 'password/request/code/',
        'password_reset': 'password/reset/',
        'user_review_list': 'user/{user_id}/review/',
        'user_review': 'user/{user_id}/review/{review_id}/',
        'wine_review': 'wine/{wine_id}/review/',
        'drink_review': 'drink/{drink_id}/review/',
    })


def test_review_list(user, api):
    resp = user.get_json(api.user_review_list(user_id=user1.id), {'page_size': 2})
```




### PropsMeta

You can find source in `fan_tools/testing/meta.py`.

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


## fan_tools.unix helpers

Basic unix helpers

* run - run command in shell
* succ - wrapper around `run` with return code and stderr check
* wait_socket - wait for socket awailable (eg. you can wait for postgresql with `wait_socket('localhost', 5432)`
* asucc - asynchronous version of `succ` for use with `await`. supports realtime logging
* source - acts similar to bash 'source' or '.' commands.
* cd - contextmanager to do something with temporarily changed directory

#### interpolate_sysenv

Format string with system variables + defaults.

```python
PG_DEFAULTS = {
    'PGDATABASE': 'postgres',
    'PGPORT': 5432,
    'PGHOST': 'localhost',
    'PGUSER': 'postgres',
    'PGPASSWORD': '',
    }
DSN = interpolate_sysenv('postgresql://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/{PGDATABASE}', PG_DEFAULTS)
```


## fan_tools.fan_logging.JSFormatter

Enable json output with additional fields, suitable for structured logging into ELK or similar solutions.

Accepts `env_vars` key with environmental keys that should be included into log.

```python
# this example uses safe_logger as handler (pip install safe_logger)
import logging
import logging.config


LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'json': {
            '()': 'fan_tools.fan_logging.JSFormatter',
            'env_vars': ['HOME'],
        },
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'DEBUG',
            'class': 'safe_logger.TimedRotatingFileHandlerSafe',
            'filename': 'test_json.log',
            'when': 'midnight',
            'interval': 1,
            'backupCount': 30,
            'formatter': 'json',
            },
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'DEBUG',
        },
    },
}

logging.config.dictConfig(LOGGING)
log = logging.getLogger('TestLogger')

log.debug('test debug')
log.info('test info')
log.warn('test warn')
log.error('test error')
```


## fan_tools.mon_server.MetricsServer

FastAPI based server that servers metrics in prometheus format.

```
import uvicorn

from fan_tools.mon_server.certs import update_certs_loop

app = FastAPI()
mserver = MetricsServer(app)
mserver.add_task(update_certs_loop, hosts=['perfectlabel.io', 'robopickles.com'])
uvicorn.run(app, host='0.0.0.0', port=os.environ.get('MONITORING_PORT', 8000))
```


## fan_tools.backup

There are two backup helpers: `fan_tools.backup.s3.S3backup` and `fan_tools.backup.gcloud.GCloud`

We're assuming that backup script has access to backup execution and dump directory.

Default setup includes support for docker container that access DB.

By default script provides interface for monitoring (last backup date).

`fan_tools.backup.s3.S3backup` provides external script called `fan_s3_backup` that has accepts some configuration via environmental variables.

* *ENABLE_BACKUP* - you need enable this by setting to non `false` value, default: false
* *BACKUP_DB_CONTAINER* - container for backup command execution
* *BACKUP_DB_SCRIPT* - command for exectuion on db server from above. default: `/create_backup.py`
* *BACKUP_COMMAND* - overrides all above
*  `-b/--bucket` - to define bucket. default for s3: environmental variable *AWS_BACKUP_BUCKET*
* *BACKUP_PREFIX* or `-p/--prefix` - directory backup prefix, usually it is subfolder for dumps, default: `backups/`
* `-d/--daemonize` - should we run in daemonized mode
* *MONITORING_PORT* - port for listen when run in daemonized mode. default: 80

S3 specific:

* *AWS_BACKUP_KEY*
* *AWS_BACKUP_SECRET*
* *AWS_BACKUP_BUCKET*



## fan_tools.drf.serializers.EnumSerializer

Allow you to deserealize incoming strings into `Enum` values.
You should add `EnumSerializer` into your serializers by hand.

```python
from enum import IntEnum

from django.db import models
from rest_framework import serializers

from fan_tools.drf.serializers import EnumSerializer


class MyEnum(IntEnum):
  one = 1
  two = 2

class ExampleModel(models.Model):
  value = models.IntegerField(choices=[(x.name, x.value) for x in MyEnum])

class ExampleSerializer(serializers.ModelSerializer):
  value = EnumSerializer(MyEnum)

# this allows you to post value as: {'value': 'one'}
```

Due to `Enum` and `IntegerField` realizations you may use `Enum.value` in querysets

```python
ExampleModel.objects.filter(value=MyEnum.two)
```

## fan_tools.django.log_requests.LoggerMiddleware

LoggerMiddleware will log request meta + raw post data into log.

For django<1.10 please use `fan_tools.django.log_requests.DeprecatedLoggerMiddleware`


## fan_tools.django.request_uniq

Decorator adds a unique for each uwsgi request dict as first function
 argument.
For tests mock `_get_request_unique_cache`


## fan_tools.django.call_once_on_commit

Make function called only once on transaction commit. Here is examples
 where function `do_some_useful` will be called only once after
 transaction has been committed.
```python
class SomeModel(models.Model):
    name = IntegerField()

@call_once_on_commit
def do_some_useful():
    pass


def hook(sender, instance, **kwargs):
    do_some_useful()

models.signals.post_save.connect(hook, sender=SomeModel)

with transaction.atomic():
    some_model = SomeModel()
    some_model.name = 'One'
    some_model.save()
    some_model.name = 'Two'
    some_model.save()
```

For tests with nested transactions (commit actually most times is not
 called) it is useful to override behaviour `call_once_on_commit`
 when decorated function executed right in place where it is called.
 To do so mock `on_commit` function. Example pytest fixture:
```
@pytest.fixture(scope='session', autouse=True)
def immediate_on_commit():
    def side_effect():
        return lambda f: f()

    with mock.patch('fan_tools.django.on_commit', side_effect=side_effect) as m:
        yield m

```

## fan_tools.django.fields.ChoicesEnum

Used for choices attribute for in model field

```
class FooBarEnum(ChoicesEnum):
    foo = 1
    bar = 2

class ExampleModel(models.Model):
    type = models.IntegerField(choices=FooBarEnum.get_choices())
```


## fan_tools.django.db.utils.set_word_similarity_threshold

Allow to set postgres trigram word similarity threshold for default django database connection

```
set_word_similarity_threshold(0.4)
```


## fan_tools.django.contrib.postgres.models.LTreeModel

Django Model containing postgres ltree

```
class LTreeExampleModel(LTreeModel):
```


## fan_tools.django.contrib.postgres.fields.LTreeDescendants

Lookup for postgres ltree descendants

```
LTreeExampleModel.objects.filter(path__descendants='root.level1')
```

## fan_tools.django.contrib.postgres.fields.LTreeNlevel

Lookup for postgres ltree by level depth

```
LTreeExampleModel.objects.filter(path__nlevel=2)
```

## fan_tools.django.db.pgfields.SimilarityLookup

Postgres `text %> text` operator

```
# Add this import to models.py (file should be imported before lookup usage)
import fan_tools.django.db.pgfields  # noqa

Books.objects.filter(title__similar='Animal Farm')
```

## fan_tools.django.db.pgfields.WordSimilarity

Postgres `text1 <<-> text2` operator. It returns `1 - word_similarity(text1, text2)`

```
from django.db.models import Value, F

similarity = WordSimilarity(Value('Animal Farm'), F('title'))
Books.objects.annotate(similarity=similarity)
```

## fan_tools.drf.filters.NumberInFilter

Django filter that match if integer is in the integers list separated by comma

```
class ExampleFilterSet(FilterSet):
    example_values = NumberInFilter(field_name='example_value', lookup_expr='in')
```

## fan_tools.django.mail.Mail

Send text and html emails using django templates.

```
Mail(
    recipient_list=[user.email],
    template_name='user/emails/reset_password',
    context={
        'frontend_url': settings.FRONTEND_URL,
    },
).send()
```

## fan_tools.django.url.build_absolute_uri

Get domain section of absolute url of current page using django request object.

```
build_absolute_uri(request)
```


## fan_tools.drf.forms.use_form

Helps to use power of serializers for simple APIs checks.


```python
from rest_framework import serializers
from rest_framework.decorators import api_view
from fan_tools.drf import use_form


class SimpleForm(serializers.Serializer):
    test_int = serializers.IntegerField()
    test_str = serializers.CharField()


@api_view(['GET'])
@use_form(SimpleForm)
def my_api(data):
    print(f'Data: {data["test_int"]} and {data["test_str"]}')
```

## fan_tools.drf.pagination.ApiPageNumberPagination

Allow turn off pagination by specifying zero page_zize.

```
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'fan_tools.drf.pagination.ApiPageNumberPagination',
    ...
}
```

## fan_tools.rest_framework.renderers.ApiRenderer

Pretty Django Rest Framework API renderer with error codes.

```
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'fan_tools.drf.renderers.ApiRenderer',
    },
    ...
}
```

## fan_tools.rest_framework.handlers.api_exception_handler

Pretty Django Rest Framework API exception handler with error codes.

```
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'fan_tools.drf.handlers.api_exception_handler',
    ...
}
```

## fan_tools.drf.asserts.assert_validation_error

Helper assert function to be used in tests to match the validation error codes.

```
assert_validation_error(response, 'email', 'unique')
```

## fan_tools.aio_utils.DbRecordsProcessorWorker

Asyncio worker which wait for new records in postgres db table and process them.

## fan_tools.aio_utils.dict_query/sql_update
aiopg shortcuts


## fan_tools.python.execfile

Backport of python's 2 `execfile` function.

Usage: execfile('path/to/file.py', globals(), locals())

Returns: True if file exists and executed, False if file doesn't exist


## fan_tools.doc_utils.fan_sphinx

Sphinx extensions to generate documentation for django restframework serializers and examples for http requests.

In order to use them specify dependency for package installation:
```
pip install fan_tools[doc_utils]
```

Usage:
```
# Add to Sphinx conf.py
extensions = [
    # ...
    'fan_tools.doc_utils.fan_sphinx.dyn_serializer',
    'fan_tools.doc_utils.fan_sphinx.http_log'
]
```

## Commands

### fan_env_yaml

Convert template yaml with substituion of `%{ENV_NAME}` strings to appropriate environment variables.

Usage: `fan_env_yaml src_file dst_file`


### fan_ci_script

Helper to run default CI pipeline. Defaults are set up for [giltab defaults](https://docs.gitlab.com/ee/ci/variables/#predefined-variables-environment-variables). Includes stages:

* build docker image with temporary name (commit sha by default)
* run tests (optional)
* push branch (by default only for master and staging branches)
* push tag, if there are tags
* cache image with common name
* delete image with temporary name

It's optimized for parallel launches, so you need to use unique temporary name (`--temp-name`). We want keep our system clean if possible, so we'll delete this tag in the end. But we don't want to repeat basic steps over and over, so we will cache image with common cache name (`--cache-name`), it will remove previous cached image.

### fan_wait

Wait for socket awailable/not-awailable with timeout.

```
# Wait until database port up for 180 seconds
fan_wait -t 180 postgres 5432

# Wait until nginx port down for 30 seconds
fan_wait -t 30 nginx 80
```

### run_filebeat

* checks environmental variables `-e KEY=VALUE -e KEY2=VALUE2`
* converts yaml template `fan_env_yaml {TEMPLATE} /tmp/filebeat.yml`
* run `/usr/bin/filebeat /tmp/filebeat.yml`

```
run_filebeat -e CHECKME=VALUE path_to_template
```


### doc_serializer

* output rst with list of serializers
* generates documentation artifacts for serializers

```
usage: doc_serializer [-h] [--rst] [--artifacts]

Parse serializers sources

optional arguments:
  -h, --help   show this help message and exit
  --rst        Output rst with serializers
  --artifacts  Write serializers artifacts
```


### image_utils.Transpose

Save rotated by exif tag images. Some browsers/applications don't respect this tag, 
so it is easier to do that explicitly.

```python
class Image(models.Model):
    uploaded_by = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)

    image = models.ImageField(blank=True, upload_to=image_upload_to)
    thumb_image = models.ImageField(blank=True, upload_to=thumb_upload_to)

    full_url = models.CharField(blank=True, max_length=255)
    thumb_url = models.CharField(blank=True, max_length=255)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

class ImageSerializer(ModelSerializer):
    class Meta:
        model = Image
        fields = ['id', 'created', 'updated', 'full_url', 'thumb_url']

class UploadImageView(views.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        image_data = request.data['image']
        # Fix an image orientation based on exif and remove exif from the resulted image.
        transformed_image = Transpose().process(image_data)
        obj = Image.objects.create(uploaded_by=request.user, image=transformed_image)
        obj.full_url = obj.image.url
        obj.save()

        s = ImageSerializer(instance=obj)
        return Response(s.data)
```


### fan_tools.metrics

Helper to send metrics. [Example for datadog](examples/send_dd_metric.py)

Usually you want to setup some kind of notification for metric with name `error_metric`. It is sent by `send_error_metric`.


For DataDog your metric query will look like:

```
sum:error_metric{service:prod*} by {error_type,service}.as_count()
```


# development

```bash
# keep docker container
tox -e py311-django40 -- --keep-db django_tests
tox -e py311-django40 -- --keep-db --docker-skip django_tests
```
