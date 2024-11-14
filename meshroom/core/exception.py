#!/usr/bin/env python
# coding:utf-8


class MeshroomException(Exception):
    """ Base class for Meshroom exceptions """
    pass


class GraphException(MeshroomException):
    """ Base class for Graph exceptions """
    pass


class GraphCompatibilityError(GraphException):
    """
    Raised when node compatibility issues occur when loading a graph.
    
    Args:
        filepath: The path to the file that caused the error.
        issues: A dictionnary of node names and their respective compatibility issues.
    """
    def __init__(self, filepath, issues: dict[str, str]) -> None:
        self.filepath = filepath
        self.issues = issues
        msg = f"Compatibility issues found when loading {self.filepath}: {self.issues}"
        super().__init__(msg)


class UnknownNodeTypeError(GraphException):
    """
    Raised when asked to create a unknown node type.
    """
    def __init__(self, nodeType, msg=None):
        msg = "Unknown Node Type: " + nodeType
        super(UnknownNodeTypeError, self).__init__(msg)
        self.nodeType = nodeType


class NodeUpgradeError(GraphException):
    def __init__(self, nodeName, details=None):
        msg = "Failed to upgrade node {}".format(nodeName)
        if details:
            msg += ": {}".format(details)
        super(NodeUpgradeError, self).__init__(msg)


class GraphVisitMessage(GraphException):
    """ Base class for sending messages via exceptions during a graph visit. """
    pass


class StopGraphVisit(GraphVisitMessage):
    """ Immediately interrupt graph visit. """
    pass


class StopBranchVisit(GraphVisitMessage):
    """ Immediately stop branch visit. """
    pass
