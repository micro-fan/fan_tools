import os
import json
from itertools import chain
from pprint import pformat
from urllib.parse import unquote, urlencode

from jinja2 import Template
from docutils.parsers.rst import Directive

from .parse_mixin import ParseMixin


TMPL = Template('''
.. sourcecode:: http

   {{method|upper}} {{path}}{% if query %}?{{query}}{% endif %} HTTP/1.1{% if payload is not none %}
   Content-Type: text/javascript

   {{payload | indent(3, False)}}{% endif %}


.. sourcecode:: http

   HTTP/1.1 {{status_code}} {{status_text}}
   Content-Type: text/javascript

   {{response | indent(3, False)}}
''')


class HttpLog(Directive, ParseMixin):
    required_arguments = 1
    has_content = True

    def format(self, s):
        if isinstance(s, str):
            return s
        elif s is not None:
            return pformat(s, indent=1)

    def add_record(self, record):
        record['response'] = self.format(record['response'])
        record['payload'] = self.format(record['payload'])
        query = record.get('query') or ''
        if isinstance(query, str):
            record['query'] = unquote(query)
        elif isinstance(query, dict):
            record['query'] = unquote(urlencode(query))

        return self.parse_lines(TMPL.render(**record).split('\n'))

    def run(self):
        artifact_path = os.environ.get('DOCS_ROOT', './.doc')
        full_path = '{}.json'.format(os.path.join('../', artifact_path, self.arguments[0]))
        with open(full_path) as f:
            records = json.load(f)
        ret = chain(*(self.add_record(record) for record in records))
        return list(ret)


def setup(app):
    app.add_directive('http_log', HttpLog)
    return {'version': '0.0.1'}
