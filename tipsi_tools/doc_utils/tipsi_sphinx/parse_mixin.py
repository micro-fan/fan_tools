from docutils.parsers.rst import Directive
from docutils.statemachine import StringList
from docutils import nodes


class ParseMixin:
    """
    Providing ability to generate nodes from plain text rst-strings.
    It's easier sometimes to generate rst from templates without manual
    work with nodes.
    """

    def rst_lines(self, lines):
        self.state_machine.insert_input(lines, '<src>')

    def parse_lines(self, lines):
        node = nodes.Element('')
        line = StringList(lines, '<src>')
        self.state.nested_parse(line, self.content_offset, node)
        return node.children

    def parse(self, line):
        return self.parse_lines([line])[0]
