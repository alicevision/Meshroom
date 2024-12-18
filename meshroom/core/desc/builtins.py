""" Defines the Built in Plugins.
"""
from .node import InputNode, AttributeFactory, Traits


class Backdrop(InputNode):
    """ A Backdrop for other nodes.
    """

    internalInputs = AttributeFactory.getInternalParameters(Traits.RESIZABLE)

    category = "Utils"
