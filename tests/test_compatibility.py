#!/usr/bin/env python
# coding:utf-8
import tempfile

import os
import pytest

import meshroom.core
from meshroom.core import desc, registerNodeType, unregisterNodeType
from meshroom.core.exception import NodeUpgradeError
from meshroom.core.graph import Graph, loadGraph
from meshroom.core.node import CompatibilityNode, CompatibilityIssue, Node


class SampleNodeV1(desc.Node):
    """ Version 1 Sample Node """
    inputs = [
        desc.File(name='input', label='Input', description='', value='', uid=[0],),
        desc.StringParam(name='paramA', label='ParamA', description='', value='', uid=[])  # No impact on UID
    ]
    outputs = [
        desc.File(name='output', label='Output', description='', value=desc.Node.internalFolder, uid=[])
    ]


class SampleNodeV2(desc.Node):
    """ Changes from V1:
        * 'input' has been renamed to 'in'
    """
    inputs = [
        desc.File(name='in', label='Input', description='', value='', uid=[0],),
        desc.StringParam(name='paramA', label='ParamA', description='', value='', uid=[])  # No impact on UID
    ]
    outputs = [
        desc.File(name='output', label='Output', description='', value=desc.Node.internalFolder, uid=[])
    ]


def test_unknown_node_type():
    """
    Test compatibility behavior for unknown node type.
    """
    registerNodeType(SampleNodeV1)
    g = Graph('')
    n = g.addNewNode("SampleNodeV1", input="/dev/null", paramA="foo")
    graphFile = os.path.join(tempfile.mkdtemp(), "test_unknown_node_type.mg")
    g.save(graphFile)
    internalFolder = n.internalFolder
    nodeName = n.name
    unregisterNodeType(SampleNodeV1)

    # reload file
    g = loadGraph(graphFile)
    os.remove(graphFile)

    assert len(g.nodes) == 1
    n = g.node(nodeName)
    # SampleNodeV1 is now an unknown type
    # check node instance type and compatibility issue type
    assert isinstance(n, CompatibilityNode)
    assert n.issue == CompatibilityIssue.UnknownNodeType
    # check if attributes are properly restored
    assert len(n.attributes) == 3
    assert n.input.isInput
    assert n.output.isOutput
    # check if internal folder
    assert n.internalFolder == internalFolder

    # upgrade can't be perform on unknown node types
    assert not n.canUpgrade
    with pytest.raises(NodeUpgradeError):
        g.upgradeNode(nodeName)


def test_description_conflict():
    """
    Test compatibility behavior for conflicting node descriptions.
    """
    registerNodeType(SampleNodeV1)

    g = Graph('')
    n = g.addNewNode("SampleNodeV1")
    graphFile = os.path.join(tempfile.mkdtemp(), "test_description_conflict.mg")
    g.save(graphFile)
    internalFolder = n.internalFolder
    nodeName = n.name

    # replace SampleNodeV1 by SampleNodeV2
    # 'SampleNodeV1' is still registered but implementation has changed
    meshroom.core.nodesDesc[SampleNodeV1.__name__] = SampleNodeV2

    # reload file
    g = loadGraph(graphFile)
    os.remove(graphFile)

    assert len(g.nodes) == 1
    n = g.node(nodeName)
    # Node description clashes between what has been saved
    assert isinstance(n, CompatibilityNode)
    assert n.issue == CompatibilityIssue.DescriptionConflict
    assert len(n.attributes) == 3
    assert hasattr(n, "input")
    assert not hasattr(n, "in")
    assert n.internalFolder == internalFolder

    # perform upgrade
    g.upgradeNode(nodeName)
    n = g.node(nodeName)

    assert isinstance(n, Node)
    assert not hasattr(n, "input")
    assert hasattr(n, "in")
    # check uid has changed (not the same set of attributes)
    assert n.internalFolder != internalFolder
    unregisterNodeType(SampleNodeV1)


def test_upgradeAllNodes():
    registerNodeType(SampleNodeV1)
    registerNodeType(SampleNodeV2)

    g = Graph('')
    n1 = g.addNewNode("SampleNodeV1")
    n2 = g.addNewNode("SampleNodeV2")
    n1Name = n1.name
    n2Name = n2.name
    graphFile = os.path.join(tempfile.mkdtemp(), "test_description_conflict.mg")
    g.save(graphFile)

    # make SampleNodeV2 an unknown type
    unregisterNodeType(SampleNodeV2)
    # replace SampleNodeV1 by SampleNodeV2
    meshroom.core.nodesDesc[SampleNodeV1.__name__] = SampleNodeV2

    # reload file
    g = loadGraph(graphFile)
    os.remove(graphFile)

    # both nodes are CompatibilityNodes
    assert len(g.compatibilityNodes) == 2
    assert g.node(n1Name).canUpgrade      # description conflict
    assert not g.node(n2Name).canUpgrade  # unknown type

    # upgrade all upgradable nodes
    g.upgradeAllNodes()

    # only the node with an unknown type has not been upgraded
    assert len(g.compatibilityNodes) == 1
    assert n2Name in g.compatibilityNodes.keys()

    unregisterNodeType(SampleNodeV1)
