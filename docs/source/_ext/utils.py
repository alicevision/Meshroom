from myst_parser.docutils_ import Parser
from myst_parser.mdit_to_docutils.base import make_document


def md_to_docutils(text):
    parser = Parser()
    doc = make_document(parser_cls=Parser)
    parser.parse(text, doc)
    return doc


def get_link_key(node):
    link_keys = ['uri', 'refuri', 'refname']
    for key in link_keys:
        if key in node.attributes.keys():
            return key
    return None
