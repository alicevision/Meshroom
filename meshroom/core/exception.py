#!/usr/bin/env python
# coding:utf-8


class MeshroomException(Exception):
    """ Base class for Meshroom exceptions """
    pass


class GraphException(MeshroomException):
    """ Base class for Graph exceptions """
    pass


class UnknownNodeTypeError(GraphException):
    """
    Raised when asked to create a unknown node type.
    """
    def __init__(self, nodeType):
        msg = "Unknown Node Type: " + nodeType
        super(UnknownNodeTypeError, self).__init__(msg)
        self.nodeType = nodeType
