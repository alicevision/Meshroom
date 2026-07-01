# -*- coding: utf-8 -*-

"""
Functions that are designed to provide a simple interface
to Meshroom scenes. This can be used to parse a scene and
get infos about the scene, about specific nodes, etc.
"""

import logging
from typing import Optional

from meshroom.core import graph as meshroomGraph
from meshroom.core.graph import Graph
from meshroom.core.node import BaseNode, BackdropNode
from meshroom.core.attribute import Attribute


LOGGER = logging.getLogger("MeshroomApi")


def loadGraph(filePath, strictCompatibility=False) -> Graph:
    g = meshroomGraph.loadGraph(filePath, strictCompatibility=strictCompatibility)
    compatibilityNodesNames = [n.name for n in g._compatibilityNodes]
    if compatibilityNodesNames:
        LOGGER.warning(f"Scene ({filePath}) loaded with compatibility nodes : {compatibilityNodesNames}")
    return g


def getNodes(graph: Graph, filterTypes: Optional[list[str]]=None) -> list[BaseNode]:
    nodes: list[BaseNode] = [n for n in graph.nodes]
    if filterTypes:
        nodes = [n for n in nodes if n.nodeType in filterTypes]
    return nodes


def getBackdropNodes(graph: Graph) -> list[BackdropNode]:
    return getNodes(graph, filterTypes="Backdrop")


def getNode(graph: Graph, instanceName: str) -> BaseNode:
    nodes = getNodes(graph)
    for node in nodes:
        if node.name == instanceName:
            return node
    return None


def getNodesInsideBackdrop(graph: Graph, backdropNode: BackdropNode):
    """ List nodes inside a backdrop node
    
    HACK: Except for Backdrop nodes we don't know nodes height and width.
    - As of now the width is fixed to 160 so we will use this
    - For the height the node header has an height of approximately 20 and it will 
    likely not change. A node without any exposed param will be at least the double so 
    we will take a height of 40.

    This might not work well, but this will work well enough for controlled cases.
    """
    
    class Rect:
        def __init__(self, node):
            self.x1 = node.x
            self.y1 = node.y
            w = node.getNodeWidth() or 160
            self.x2 = w + self.x1
            h = node.getNodeHeight() or 40
            self.y2 = h + self.y1

    backdropRect = Rect(backdropNode)

    def isNodeInsideBackdrop(node: BaseNode):
        nodeRect = Rect(node)
        isinside = \
            backdropRect.x1 < nodeRect.x1 < nodeRect.x2 < backdropRect.x2 and \
            backdropRect.y1 < nodeRect.y1 < nodeRect.y2 < backdropRect.y2
        return isinside

    nodes = [n for n in getNodes(graph) if n.name != backdropNode.name]
    nodesInside = [n for n in nodes if isNodeInsideBackdrop(n)]
    return nodesInside


def getNodeAttributes(node: BaseNode, internalAttributes=False, allAttributes=False) -> list[Attribute]:
    attributes = []
    if not internalAttributes or allAttributes:
        attributes.extend([v for v in node.getAttributes().values()])
    if internalAttributes or allAttributes:
        attributes.extend([v for v in node.getInternalAttributes().values()])
    return attributes
