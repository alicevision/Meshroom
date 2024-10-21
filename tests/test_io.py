#!/usr/bin/env python
# coding:utf-8

import os
import tempfile

from meshroom.core import desc, registerNodeType
from meshroom.core.graph import Graph, loadGraph
from meshroom.core.node import CompatibilityNode

def test_io_group_connections():
    """
    Ensure that connecting attributes that are part of GroupAttributes does not cause
    their nodes to have CompatibilityIssues when re-opening them.
    """
    graph = Graph("Connections between GroupAttributes")

    # Create two "GroupAttributes" nodes with their default parameters
    nodeA = graph.addNewNode("GroupAttributes")
    nodeB = graph.addNewNode("GroupAttributes")

    # Connect attributes within groups at different depth levels
    graph.addEdges(
        (nodeA.firstGroup.firstGroupIntA, nodeB.firstGroup.firstGroupIntA),
        (nodeA.firstGroup.nestedGroup.nestedGroupFloat, nodeB.firstGroup.nestedGroup.nestedGroupFloat)
    )

    # Save the graph in a file
    graphFile = os.path.join(tempfile.mkdtemp(), "test_io_group_connections.mg")
    graph.save(graphFile)
    
    # Reload the graph
    graph = loadGraph(graphFile)

    # Ensure the nodes are not CompatibilityNodes
    for node in graph.nodes:
        assert not isinstance(node, CompatibilityNode)
