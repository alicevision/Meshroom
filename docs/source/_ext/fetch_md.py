import os
from docutils.nodes import SparseNodeVisitor
from docutils.parsers.rst import Directive
from myst_parser.docutils_ import Parser
from myst_parser.mdit_to_docutils.base import make_document


class Relinker(SparseNodeVisitor):

    @staticmethod
    def get_link_key(node):
        link_keys = ['uri', 'refuri', 'refname']
        for key in link_keys:
            if key in node.attributes.keys():
                return key
        return None

    def relink(self, node, base_dir):
        key = Relinker.get_link_key(node)
        if key is None:
            return
        link = node.attributes[key]
        if link.startswith('http') or link.startswith('mailto'):
            return
        if link.startswith('/'):
            link = link[1:]
        node.attributes[key] = base_dir+'/'+link

    def visit_image(self, node):
        self.relink(node, os.getenv('PROJECT_DIR'))


class FetchMd(Directive):

    required_arguments = 2

    def arg_path(self):
        if self.arguments[0] == ':file:':
            return self.arguments[1]

    def run(self):
        path = os.path.abspath(os.getenv('PROJECT_DIR') + '/' + self.arg_path())
        result = []
        try:
            with open(path) as file:
                parser = Parser()
                text = file.read()
                doc = make_document(parser_cls=Parser)
                parser.parse(text, doc)
                relinker = Relinker(doc)
                doc.walk(relinker)
                result.append(doc[0])
        except FileNotFoundError:
            pass
        return result


def setup(app):
    app.add_directive('fetch_md', FetchMd)

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True
    }
