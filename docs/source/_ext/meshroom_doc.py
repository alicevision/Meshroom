# Sphinx extension defining the meshroom_doc directive
#
# Goal:
# create specific documentation content for meshroom objects
#
# Usage:
# .. meshroom_doc::
#    :module: module_name
#    :class: class_name
#
# Note:
# for now this tool focuses only on meshroom nodes

from docutils.parsers.rst import Directive
from utils import md_to_docutils

import importlib
from meshroom.core import desc


class MeshroomDoc(Directive):

    required_arguments = 4

    def parse_args(self):
        module_name = self.arguments[self.arguments.index(':module:')+1]
        class_name = self.arguments[self.arguments.index(':class:')+1]
        return (module_name, class_name)

    def run(self):
        result = []
        # Import module and class
        module_name, class_name = self.parse_args()
        module = importlib.import_module(module_name)
        node_class = getattr(module, class_name)
        # Class inherits desc.Node
        if issubclass(node_class, desc.Node):
            node = node_class()
            # Category
            doc = md_to_docutils('**Category**: {}'.format(node.category))
            result.extend(doc.children)
            # Documentation
            doc = md_to_docutils(node.documentation)
            result.extend(doc.children)
            # Inputs
            text_inputs = '**Inputs**: \n'
            for attr in node.inputs:
                text_inputs += '- {} ({})\n'.format(attr._name, attr.__class__.__name__)
            doc = md_to_docutils(text_inputs)
            result.extend(doc.children)
            # Outputs
            text_outputs = '**Outputs**: \n'
            for attr in node.outputs:
                text_outputs += '- {} ({})\n'.format(attr._name, attr.__class__.__name__)
            doc = md_to_docutils(text_outputs)
            result.extend(doc.children)
        return result


def setup(app):
    app.add_directive("meshroom_doc", MeshroomDoc)
    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
