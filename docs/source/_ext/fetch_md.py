# Sphinx extension defining the fetch_md directive
#
# Goal:
# include the content of a given markdown file
#
# Usage:
# .. fetch_md:: path/to/file.md
# the filepath is relative to the project base directory
#
# Note:
# some markdown files contain links to other files that belong to the project
# since those links are relative to the file location, they are no longer valid in the new context
# therefore we try to update these links but it is not always possible

import os
from docutils.nodes import SparseNodeVisitor
from docutils.parsers.rst import Directive
from utils import md_to_docutils, get_link_key

# Python2 compatibility
try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError


class Relinker(SparseNodeVisitor):

    def relink(self, node, base_dir):
        key = get_link_key(node)
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

    required_arguments = 1

    def run(self):
        path = os.path.abspath(os.getenv('PROJECT_DIR')+'/'+self.arguments[0])
        result = []
        try:
            with open(path) as file:
                text = file.read()
                doc = md_to_docutils(text)
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
