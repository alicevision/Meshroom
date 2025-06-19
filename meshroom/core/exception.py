#!/usr/bin/env python


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
        super().__init__(msg)
        self.nodeType = nodeType


class NodeUpgradeError(GraphException):
    def __init__(self, nodeName, details=None):
        msg = f"Failed to upgrade node {nodeName}"
        if details:
            msg += f": {details}"
        super().__init__(msg)


class GraphVisitMessage(GraphException):
    """ Base class for sending messages via exceptions during a graph visit. """
    pass


class StopGraphVisit(GraphVisitMessage):
    """ Immediately interrupt graph visit. """
    pass


class StopBranchVisit(GraphVisitMessage):
    """ Immediately stop branch visit. """
    pass


class AttributeCompatibilityError(GraphException):
    """ 
    Raised when trying to connect attributes that are incompatible
    """

class ConnectionError(GraphException):
    """
    Raised when trying to connect attributes
    """

class InvalidEdgeError(GraphException):
    """Raised when an edge between two attributes cannot be created."""

    def __init__(self, srcAttrName: str, dstAttrName: str, msg: str) -> None:
        super().__init__(f"Failed to connect {srcAttrName}->{dstAttrName}: {msg}")