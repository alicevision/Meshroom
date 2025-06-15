#!/usr/bin/env python
# coding:utf-8

import os
import tempfile

from meshroom.core.graph import Graph, loadGraph
from meshroom.core.node import CompatibilityNode
from meshroom.core.attribute import GroupAttribute

GROUPATTRIBUTES_FIRSTGROUP_NB_CHILDREN = 8  # 1 int, 1 exclusive choice param, 1 choice param, 1 bool, 1 group, 1 float nested in the group, 2 lists
GROUPATTRIBUTES_FIRSTGROUP_NESTED_NB_CHILDREN = 1  # 1 float
GROUPATTRIBUTES_OUTPUTGROUP_NB_CHILDREN = 1  # 1 bool
GROUPATTRIBUTES_FIRSTGROUP_DEPTHS = [1, 1, 1, 1, 1, 2, 1, 1]

def test_saveLoadGroupConnections():
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


def test_groupAttributesFlatChildren():
    """
    Check that the list of static flat children is correct, even with list elements.
    """
    graph = Graph("Children of GroupAttributes")

    # Create two "GroupAttributes" nodes with their default parameters
    node = graph.addNewNode("GroupAttributes")

    intAttr = node.attribute("exposedInt")
    assert not isinstance(intAttr, GroupAttribute)
    assert len(intAttr.flatStaticChildren) == 0  # Not a Group, cannot have any child

    inputGroup = node.attribute("firstGroup")
    assert isinstance(inputGroup, GroupAttribute)
    assert len(inputGroup.flatStaticChildren) == GROUPATTRIBUTES_FIRSTGROUP_NB_CHILDREN

    # Add an element to a list within the group and check the number of children hasn't changed
    groupedList = node.attribute("firstGroup.singleGroupedList")
    groupedList.insert(0, 30)
    assert len(groupedList.flatStaticChildren) == 0  # Not a Group, elements are not counted as children
    assert len(inputGroup.flatStaticChildren) == GROUPATTRIBUTES_FIRSTGROUP_NB_CHILDREN

    nestedGroup = node.attribute("firstGroup.nestedGroup")
    assert isinstance(nestedGroup, GroupAttribute)
    assert len(nestedGroup.flatStaticChildren) == GROUPATTRIBUTES_FIRSTGROUP_NESTED_NB_CHILDREN

    outputGroup = node.attribute("outputGroup")
    assert isinstance(outputGroup, GroupAttribute)
    assert len(outputGroup.flatStaticChildren) == GROUPATTRIBUTES_OUTPUTGROUP_NB_CHILDREN


def test_groupAttributesDepthLevels():
    """
    Check that the depth level of children attributes is correctly set.
    """
    graph = Graph("Children of GroupAttributes")

    # Create two "GroupAttributes" nodes with their default parameters
    node = graph.addNewNode("GroupAttributes")
    inputGroup = node.attribute("firstGroup")
    assert isinstance(inputGroup, GroupAttribute)
    assert inputGroup.depth == 0  # Root level

    cnt = 0
    for child in inputGroup.flatStaticChildren:
        assert child.depth == GROUPATTRIBUTES_FIRSTGROUP_DEPTHS[cnt]
        cnt = cnt + 1
    
    outputGroup = node.attribute("outputGroup")
    assert isinstance(outputGroup, GroupAttribute)
    assert outputGroup.depth == 0
    for child in outputGroup.flatStaticChildren:  # Single element in the group
        assert child.depth == 1
    

    intAttr = node.attribute("exposedInt")
    assert not isinstance(intAttr, GroupAttribute)
    assert intAttr.depth == 0