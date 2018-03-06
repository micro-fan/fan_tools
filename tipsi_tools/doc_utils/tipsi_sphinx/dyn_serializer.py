import json
import os
from importlib import import_module

from docutils import nodes
from docutils.parsers.rst import Directive

from .parse_mixin import ParseMixin


def import_name(name):
    m_name, c_name = name.rsplit('.', 1)
    return getattr(import_module(m_name), c_name)


def p(text, *children):
    return nodes.paragraph('', text, *children)


def parse_doc(doc):
    """
    Parse docstrings to dict, it should look like:
      key: value
    """
    if not doc:
        return {}
    out = {}
    for s in doc.split('\n'):
        s = s.strip().split(':', maxsplit=1)
        if len(s) == 2:
            out[s[0]] = s[1]
    return out


class SerializerField:
    def _method_field(self, method):
        if method['method_name']:
            params = parse_doc(method['method_doc'])
            if 'type' in params:
                _type = params['type']
                return self.parse(_type) if ':any:' in _type else p(params['type'])
            return p('METHOD_NEED_TYPE_STUB: {}'.format(method['method_name']))
        return p('METHOD_FIELD_STUB')

    def _dyn_field(self, ref_name):
        return self.parse(':any:`{}`'.format(ref_name))

    def _dyn_list(self, ref_name):
        return self.parse(':any:`list[{name}] <{name}>`'.format(name=ref_name))

    @staticmethod
    def _none_field(data):
        tpl = 'FHELPER_TYPE_NOT_DESCRIBED_STUB: {} DM: {} {}'
        return p(tpl.format(data['__field__'], data['is_dyn_serializer'], data['__class__']))

    @staticmethod
    def _doc_field(doc):
        params = parse_doc(doc['model_doc'])
        if 'type' not in params:
            params = parse_doc(doc['serializer_doc'])
        return p(params['type']) if 'type' in params else None

    def __init__(self, f, directive):
        self.f = f
        self.directive = directive
        self.parse = directive.parse

    def process(self):
        field = self.f
        type_data = self.f['type']

        _type = None
        if 'primitive_type' in type_data:
            _type = p(type_data['primitive_type'])
        elif 'method_type' in type_data:
            _type = self._method_field(type_data['method_type'])
        elif 'dyn_field_type' in type_data:
            _type = self._dyn_field(type_data['dyn_field_type']['ref_name'])
        elif 'list_field_type' in type_data:
            child_type = type_data['list_field_type']
            if 'ref_name' in child_type:
                _type = self._dyn_list(type_data['list_field_type']['ref_name'])
            elif 'primitive_type' in child_type:
                p_type = child_type['primitive_type']
                _type = p('list[{}]'.format(p_type))
            else:
                pass  # TODO: Process other cases
        elif 'doc_type' in type_data:
            _type = self._doc_field(type_data['doc_type'])

        if not _type:
            _type = self._none_field(field)

        _type += nodes.Text(' ')

        if field['readonly']:
            _type += self.parse('|readonly|')[0]
        if field['write_only']:
            _type += self.parse('|writeonly|')[0]
        if field['required']:
            _type += self.parse('|required|')[0]
        if field['allow_null']:
            _type += self.parse('|nullable|')[0]
        if field.get('help_text'):
            _type += nodes.Text(' ' + field['help_text'])

        name = nodes.entry('', p(field['name']))
        _type = nodes.entry('', _type)
        content = nodes.row('', name, _type)
        return content


class DynSerializer(Directive, ParseMixin):
    required_arguments = 1
    has_content = True

    def run(self):
        artifact_path = os.environ.get('DOCS_ROOT', './.doc')
        full_path = '{}.json'.format(os.path.join('../', artifact_path, self.arguments[0]))
        with open(full_path) as f:
            obj_data = json.load(f)

        p_fields = (SerializerField(f, self).process() for f in obj_data['fields'])

        class_name = obj_data['class_name']

        fields = nodes.tbody('')
        fields.extend(p_fields)

        name = nodes.title('', '{}'.format(class_name))
        thead = nodes.thead('', nodes.row('',
                                          nodes.entry('', p('name')),
                                          nodes.entry('', p('type'))))
        tbl = nodes.table()
        tg = nodes.tgroup()
        tbl.append(tg)
        tg.append(nodes.colspec(colwidth=1))
        tg.append(nodes.colspec(colwidth=8))
        tg.append(thead)
        tg.append(fields)
        cname = 'Class: *{}.{}*'.format(obj_data['class_module'], class_name)
        param = 'Filter field: *{}*'.format(obj_data['field_param'])
        full_name = self.parse(cname)
        filter_param = self.parse(param)
        raw = nodes.section('', name, full_name, filter_param,
                            p('', nodes.topic('', tbl)))

        target = self.parse('.. _{name}:'.format(name=class_name))
        return [target, raw]


def setup(app):
    app.add_directive('dyn_serializer', DynSerializer)
    return {'version': '0.0.1'}
