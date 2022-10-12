from docutils import nodes
from docutils.parsers.rst import Directive
from myst_parser.docutils_ import Parser
from myst_parser.mdit_to_docutils.base import make_document

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
            parser = Parser()
            # Category
            doc = make_document(parser_cls=Parser)
            parser.parse('**Category**: {}'.format(node.category), doc)
            result.extend(doc.children)
            # Documentation
            doc = make_document(parser_cls=Parser)
            parser.parse(node.documentation, doc)
            result.extend(doc.children)
            # Inputs
            text_inputs = '**Inputs**: \n'
            for attr in node.inputs:
                text_inputs += '- {} ({})\n'.format(attr._name, attr.__class__.__name__)
            doc = make_document(parser_cls=Parser)
            parser.parse(text_inputs, doc)
            result.extend(doc.children)
            # Outputs
            text_outputs = '**Outputs**: \n'
            for attr in node.outputs:
                text_outputs += '- {} ({})\n'.format(attr._name, attr.__class__.__name__)
            doc = make_document(parser_cls=Parser)
            parser.parse(text_outputs, doc)
            result.extend(doc.children)
        return result


def setup(app):
    app.add_directive("meshroom_doc", MeshroomDoc)
    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
