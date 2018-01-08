#!/usr/bin/env python3

import argparse
import inspect
import json
import os
from functools import partial
from importlib import import_module

import sys
from rest_framework_dyn_serializer import DynModelSerializer

from tipsi_tools.doc_utils.tipsi_sphinx.dyn_json import serializer_doc_info


def compose(*funs):
    it = funs[-1]
    funs = funs[:-1]

    def inner(*args, **kwargs):
        for res in it(*args, **kwargs):
            for fun in funs:
                res = fun(res)
            if inspect.isgenerator(res):
                for r in res:
                    yield r
            else:
                yield res

    return inner


def get_modules(apps):
    for app in apps:
        for mod in ('serializers', 'forms'):
            try:
                yield import_module('{}.{}'.format(app, mod))
            except ImportError:
                pass
            except AttributeError:
                pass


def get_dynserializers(module):
    filters = (
        lambda i: inspect.isclass(i),
        lambda i: i != DynModelSerializer,
        lambda i: not(hasattr(i, 'Meta') and getattr(i.Meta, 'abstract', False)),
        lambda i: issubclass(i, DynModelSerializer) or getattr(i, '_write_docs', False),
    )

    for item in dir(module):
        item = getattr(module, item)
        if all(f(item) for f in filters):
            yield item


class ArtifactWriter:
    _inst = None

    def __init__(self):
        path = os.environ.get('DOCS_ROOT', './.doc')
        if not os.path.exists(path):
            os.mkdir(path)
        self.doc_root = path

    @classmethod
    def instance(cls):
        if not cls._inst:
            cls._inst = cls()
        return cls._inst

    def dump(self, data, path):
        f_name = os.path.join(self.doc_root, '{}.json'.format(path))
        with open(f_name, 'w') as f:
            json.dump(data, f)


def container_type():
    container = os.environ.get('CONTAINER_TYPE')
    if not container:
        sys.exit('Error: CONTAINER_TYPE is not defined')
    return container


def process_item(item, flags):
    path = '{}.{}'.format(item.__module__, item.__name__)
    if flags.rst:
        print('.. dyn_serializer:: {}/{}\n'.format(container_type(), path))
    if flags.artifacts:
        data = serializer_doc_info(item, path)
        ArtifactWriter.instance().dump(data, path)


def process(apps, fun):
    f = compose(get_dynserializers, get_modules)(apps)
    for s in f:
        fun(s)


parser = argparse.ArgumentParser(description='Parse serializers sources')

parser.add_argument('--rst', action='store_true', default=False,
                    help='Output rst with serializers')
parser.add_argument('--artifacts', action='store_true', default=False,
                    help='Write serializers artifacts')


def main():
    sys.path.append('.')
    args = parser.parse_args()

    if not any((args.rst, args.artifacts, )):
        parser.print_help()

    import django
    django.setup()
    from django.apps import apps

    all_apps = (app.module.__name__ for app in apps.get_app_configs())

    process(all_apps, partial(process_item, flags=args))


if __name__ == '__main__':
    main()
