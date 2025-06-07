#!/usr/bin/env python
# coding:utf-8
import tempfile
import os

import copy
from typing import Type
import pytest

from meshroom.core import desc, pluginManager
from meshroom.core.plugins import NodePlugin
from meshroom.core.exception import GraphCompatibilityError, NodeUpgradeError
from meshroom.core.graph import Graph, loadGraph
from meshroom.core.node import CompatibilityNode, CompatibilityIssue, Node

from .utils import registeredNodeTypes, overrideNodeTypeVersion, registerNodeDesc, unregisterNodeDesc


SampleGroupV1 = [
    desc.IntParam(name="a", label="a", description="", value=0, range=None),
    desc.ListAttribute(
        name="b",
        elementDesc=desc.FloatParam(name="p", label="",
                                    description="", value=0.0, range=None),
        label="b",
        description="",
    )
]

SampleGroupV2 = [
    desc.IntParam(name="a", label="a", description="", value=0, range=None),
    desc.ListAttribute(
        name="b",
        elementDesc=desc.GroupAttribute(name="p", label="",
                                        description="", groupDesc=SampleGroupV1),
        label="b",
        description="",
    )
]

# SampleGroupV3 is SampleGroupV2 with one more int parameter
SampleGroupV3 = [
    desc.IntParam(name="a", label="a", description="", value=0, range=None),
    desc.IntParam(name="notInSampleGroupV2", label="notInSampleGroupV2",
                  description="", value=0, range=None),
    desc.ListAttribute(
        name="b",
        elementDesc=desc.GroupAttribute(name="p", label="",
                                        description="", groupDesc=SampleGroupV1),
        label="b",
        description="",
    )
]


class SampleNodeV1(desc.Node):
    """ Version 1 Sample Node """
    inputs = [
        desc.File(name="input", label="Input", description="", value=""),
        desc.StringParam(name="paramA", label="ParamA", description="",
                         value="", invalidate=False)  # No impact on UID
    ]
    outputs = [
        desc.File(name="output", label="Output", description="", value="{nodeCacheFolder}")
    ]


class SampleNodeV2(desc.Node):
    """ Changes from V1:
        * 'input' has been renamed to 'in'
    """
    inputs = [
        desc.File(name="in", label="Input", description="", value=""),
        desc.StringParam(name="paramA", label="ParamA", description="",
                         value="", invalidate=False),  # No impact on UID
    ]
    outputs = [
        desc.File(name="output", label="Output", description="", value="{nodeCacheFolder}")
    ]


class SampleNodeV3(desc.Node):
    """
    Changes from V3:
        * 'paramA' has been removed'
    """
    inputs = [
        desc.File(name="in", label="Input", description="", value=""),
    ]
    outputs = [
        desc.File(name="output", label="Output", description="", value="{nodeCacheFolder}")
    ]


class SampleNodeV4(desc.Node):
    """
    Changes from V3:
        * 'paramA' has been added
    """
    inputs = [
        desc.File(name="in", label="Input", description="", value=""),
        desc.ListAttribute(name="paramA", label="ParamA",
                           elementDesc=desc.GroupAttribute(
                               groupDesc=SampleGroupV1, name="gA", label="gA", description=""),
                           description="")
    ]
    outputs = [
        desc.File(name="output", label="Output", description="", value="{nodeCacheFolder}")
    ]


class SampleNodeV5(desc.Node):
    """
    Changes from V4:
        * 'paramA' elementDesc has changed from SampleGroupV1 to SampleGroupV2
    """
    inputs = [
        desc.File(name="in", label="Input", description="", value=""),
        desc.ListAttribute(name="paramA", label="ParamA",
                           elementDesc=desc.GroupAttribute(
                               groupDesc=SampleGroupV2, name="gA", label="gA", description=""),
                           description="")
    ]
    outputs = [
        desc.File(name="output", label="Output", description="", value="{nodeCacheFolder}")
    ]


class SampleNodeV6(desc.Node):
    """
    Changes from V5:
        * 'paramA' elementDesc has changed from SampleGroupV2 to SampleGroupV3
    """
    inputs = [
        desc.File(name="in", label="Input", description="", value=""),
        desc.ListAttribute(name="paramA", label="ParamA",
                           elementDesc=desc.GroupAttribute(
                               groupDesc=SampleGroupV3, name="gA", label="gA", description=""),
                           description="")
    ]
    outputs = [
        desc.File(name="output", label="Output", description="", value="{nodeCacheFolder}")
    ]


class SampleInputNodeV1(desc.InputNode):
    """ Version 1 Sample Input Node """
    inputs = [
        desc.StringParam(name="path", label="Path", description="",
                         value="", invalidate=False)  # No impact on UID
    ]
    outputs = [
        desc.File(name="output", label="Output", description="", value="{nodeCacheFolder}")
    ]


class SampleInputNodeV2(desc.InputNode):
    """ Changes from V1:
        * 'path' has been renamed to 'in'
    """
    inputs = [
        desc.StringParam(name="in", label="path", description="",
                         value="", invalidate=False)  # No impact on UID
    ]
    outputs = [
        desc.File(name="output", label="Output", description="", value="{nodeCacheFolder}")
    ]



def replaceNodeTypeDesc(nodeType: str, nodeDesc: Type[desc.Node]):
    """Change the `nodeDesc` associated to `nodeType`."""
    pluginManager.getRegisteredNodePlugins()[nodeType] = NodePlugin(nodeDesc)


def test_unknown_node_type():
    """
    Test compatibility behavior for unknown node type.
    """
    registerNodeDesc(SampleNodeV1)
    g = Graph("")
    n = g.addNewNode("SampleNodeV1", input="/dev/null", paramA="foo")
    graphFile = os.path.join(tempfile.mkdtemp(), "test_unknown_node_type.mg")
    g.save(graphFile)
    internalFolder = n.internalFolder
    nodeName = n.name
    unregisterNodeDesc(SampleNodeV1)


    # Reload file
    g = loadGraph(graphFile)
    os.remove(graphFile)

    assert len(g.nodes) == 1
    n = g.node(nodeName)
    # SampleNodeV1 is now an unknown type
    # Check node instance type and compatibility issue type
    assert isinstance(n, CompatibilityNode)
    assert n.issue == CompatibilityIssue.UnknownNodeType
    # Check if attributes are properly restored
    assert len(n.attributes) == 3
    assert n.input.isInput
    assert n.output.isOutput
    # Check if internal folder
    assert n.internalFolder == internalFolder

    # Upgrade can't be perform on unknown node types
    assert not n.canUpgrade
    with pytest.raises(NodeUpgradeError):
        g.upgradeNode(nodeName)


def test_description_conflict():
    """
    Test compatibility behavior for conflicting node descriptions.
    """
    # Copy registered node types to be able to restore them
    originalNodeTypes = copy.deepcopy(pluginManager.getRegisteredNodePlugins())

    nodeTypes = [SampleNodeV1, SampleNodeV2, SampleNodeV3, SampleNodeV4, SampleNodeV5]
    nodes = []
    g = Graph("")

    # Register and instantiate instances of all node types except last one
    for nt in nodeTypes[:-1]:
        registerNodeDesc(nt)
        n = g.addNewNode(nt.__name__)

        if nt == SampleNodeV4:
            # Initialize list attribute with values to create a conflict with V5
            n.paramA.value = [{'a': 0, 'b': [1.0, 2.0]}]

        nodes.append(n)

    graphFile = os.path.join(tempfile.mkdtemp(), "test_description_conflict.mg")
    g.save(graphFile)

    # Reload file as-is, ensure no compatibility issue is detected (no CompatibilityNode instances)
    loadGraph(graphFile, strictCompatibility=True)

    # Offset node types register to create description conflicts
    # Each node type name now reference the next one's implementation
    for i, nt in enumerate(nodeTypes[:-1]):
        pluginManager.getRegisteredNodePlugins()[nt.__name__] = NodePlugin(nodeTypes[i + 1])

    # Reload file
    g = loadGraph(graphFile)
    os.remove(graphFile)

    assert len(g.nodes) == len(nodes)
    for srcNode in nodes:
        nodeName = srcNode.name
        compatNode = g.node(srcNode.name)
        # Node description clashes between what has been saved
        assert isinstance(compatNode, CompatibilityNode)
        assert srcNode.internalFolder == compatNode.internalFolder

        # Case by case description conflict verification
        if isinstance(srcNode.nodeDesc, SampleNodeV1):
            # V1 => V2: 'input' has been renamed to 'in'
            assert len(compatNode.attributes) == 3
            assert list(compatNode.attributes.keys()) == ["input", "paramA", "output"]
            assert hasattr(compatNode, "input")
            assert not hasattr(compatNode, "in")

            # Perform upgrade
            upgradedNode = g.upgradeNode(nodeName)
            assert isinstance(upgradedNode, Node) and \
                isinstance(upgradedNode.nodeDesc, SampleNodeV2)

            assert list(upgradedNode.attributes.keys()) == ["in", "paramA", "output"]
            assert not hasattr(upgradedNode, "input")
            assert hasattr(upgradedNode, "in")
            # Check UID has changed (not the same set of attributes)
            assert upgradedNode.internalFolder != srcNode.internalFolder

        elif isinstance(srcNode.nodeDesc, SampleNodeV2):
            # V2 => V3: 'paramA' has been removed
            assert len(compatNode.attributes) == 3
            assert hasattr(compatNode, "paramA")

            # Perform upgrade
            upgradedNode = g.upgradeNode(nodeName)
            assert isinstance(upgradedNode, Node) and \
                isinstance(upgradedNode.nodeDesc, SampleNodeV3)

            assert not hasattr(upgradedNode, "paramA")
            # Check UID is identical (paramA not part of UID)
            assert upgradedNode.internalFolder == srcNode.internalFolder

        elif isinstance(srcNode.nodeDesc, SampleNodeV3):
            # V3 => V4: 'paramA' has been added
            assert len(compatNode.attributes) == 2
            assert not hasattr(compatNode, "paramA")

            # Perform upgrade
            upgradedNode = g.upgradeNode(nodeName)
            assert isinstance(upgradedNode, Node) and \
                isinstance(upgradedNode.nodeDesc, SampleNodeV4)

            assert hasattr(upgradedNode, "paramA")
            assert isinstance(upgradedNode.paramA.attributeDesc, desc.ListAttribute)
            # paramA child attributes invalidate UID
            assert upgradedNode.internalFolder != srcNode.internalFolder

        elif isinstance(srcNode.nodeDesc, SampleNodeV4):
            # V4 => V5: 'paramA' elementDesc has changed from SampleGroupV1 to SampleGroupV2
            assert len(compatNode.attributes) == 3
            assert hasattr(compatNode, "paramA")
            groupAttribute = compatNode.paramA.attributeDesc.elementDesc

            assert isinstance(groupAttribute, desc.GroupAttribute)
            # Check that Compatibility node respect SampleGroupV1 description
            for elt in groupAttribute.groupDesc:
                assert isinstance(elt,
                                  next(a for a in SampleGroupV1 if a.name == elt.name).__class__)

            # Perform upgrade
            upgradedNode = g.upgradeNode(nodeName)
            assert isinstance(upgradedNode, Node) and \
                isinstance(upgradedNode.nodeDesc, SampleNodeV5)

            assert hasattr(upgradedNode, "paramA")
            # Parameter was incompatible, value could not be restored
            assert upgradedNode.paramA.isDefault
            assert upgradedNode.internalFolder != srcNode.internalFolder
        else:
            raise ValueError("Unexpected node type: " + srcNode.nodeType)

    # Restore original node types
    pluginManager._nodePlugins = originalNodeTypes

def test_upgradeAllNodes():
    registerNodeDesc(SampleNodeV1)
    registerNodeDesc(SampleNodeV2)
    registerNodeDesc(SampleInputNodeV1)
    registerNodeDesc(SampleInputNodeV2)

    g = Graph("")
    n1 = g.addNewNode("SampleNodeV1")
    n2 = g.addNewNode("SampleNodeV2")
    n3 = g.addNewNode("SampleInputNodeV1")
    n4 = g.addNewNode("SampleInputNodeV2")
    n1Name = n1.name
    n2Name = n2.name
    n3Name = n3.name
    n4Name = n4.name
    graphFile = os.path.join(tempfile.mkdtemp(), "test_description_conflict.mg")
    g.save(graphFile)

    # Replace SampleNodeV1 by SampleNodeV2 and SampleInputNodeV1 by SampleInputNodeV2
    pluginManager.getRegisteredNodePlugins()[SampleNodeV1.__name__] = \
        pluginManager.getRegisteredNodePlugin(SampleNodeV2.__name__)
    pluginManager.getRegisteredNodePlugins()[SampleInputNodeV1.__name__] = \
        pluginManager.getRegisteredNodePlugin(SampleInputNodeV2.__name__)

    # Make SampleNodeV2 and SampleInputNodeV2 an unknown type
    unregisterNodeDesc(SampleNodeV2)
    unregisterNodeDesc(SampleInputNodeV2)

    # Reload file
    g = loadGraph(graphFile)
    os.remove(graphFile)

    # Both nodes are CompatibilityNodes
    assert len(g.compatibilityNodes) == 4
    assert g.node(n1Name).canUpgrade      # description conflict
    assert not g.node(n2Name).canUpgrade  # unknown type
    assert g.node(n3Name).canUpgrade      # description conflict
    assert not g.node(n4Name).canUpgrade  # unknown type

    # Upgrade all upgradable nodes
    g.upgradeAllNodes()

    # Only the nodes with an unknown type have not been upgraded
    assert len(g.compatibilityNodes) == 2
    assert n2Name in g.compatibilityNodes.keys()
    assert n4Name in g.compatibilityNodes.keys()

    unregisterNodeDesc(SampleNodeV1)
    unregisterNodeDesc(SampleInputNodeV1)


def test_conformUpgrade():
    registerNodeDesc(SampleNodeV5)
    registerNodeDesc(SampleNodeV6)

    g = Graph("")
    n1 = g.addNewNode("SampleNodeV5")
    n1.paramA.value = [{"a": 0, "b": [{"a": 0, "b": [1.0, 2.0]}, {"a": 1, "b": [1.0, 2.0]}]}]
    n1Name = n1.name
    graphFile = os.path.join(tempfile.mkdtemp(), "test_conform_upgrade.mg")
    g.save(graphFile)

    # Replace SampleNodeV5 by SampleNodeV6
    pluginManager.getRegisteredNodePlugins()[SampleNodeV5.__name__] = \
        pluginManager.getRegisteredNodePlugin(SampleNodeV6.__name__)

    # Reload file
    g = loadGraph(graphFile)
    os.remove(graphFile)

    # Node is a CompatibilityNode
    assert len(g.compatibilityNodes) == 1
    assert g.node(n1Name).canUpgrade

    # Upgrade all upgradable nodes
    g.upgradeAllNodes()

    # Only the node with an unknown type has not been upgraded
    assert len(g.compatibilityNodes) == 0

    upgradedNode = g.node(n1Name)

    # Check upgrade
    assert isinstance(upgradedNode, Node) and isinstance(upgradedNode.nodeDesc, SampleNodeV6)

    # Check conformation
    assert len(upgradedNode.paramA.value) == 1

    unregisterNodeDesc(SampleNodeV5)
    unregisterNodeDesc(SampleNodeV6)


class TestGraphLoadingWithStrictCompatibility:

    def test_failsOnUnknownNodeType(self, graphSavedOnDisk):
        with registeredNodeTypes([SampleNodeV1]):
            graph: Graph = graphSavedOnDisk
            graph.addNewNode(SampleNodeV1.__name__)
            graph.save()

        with pytest.raises(GraphCompatibilityError):
            loadGraph(graph.filepath, strictCompatibility=True)


    def test_failsOnNodeDescriptionCompatibilityIssue(self, graphSavedOnDisk):
        with registeredNodeTypes([SampleNodeV1, SampleNodeV2]):
            graph: Graph = graphSavedOnDisk
            graph.addNewNode(SampleNodeV1.__name__)
            graph.save()

            replaceNodeTypeDesc(SampleNodeV1.__name__, SampleNodeV2)

            with pytest.raises(GraphCompatibilityError):
                loadGraph(graph.filepath, strictCompatibility=True)


class TestGraphTemplateLoading:

    def test_failsOnUnknownNodeTypeError(self, graphSavedOnDisk):
        with registeredNodeTypes([SampleNodeV1, SampleNodeV2]):
            graph: Graph = graphSavedOnDisk
            graph.addNewNode(SampleNodeV1.__name__)
            graph.save(template=True)

        with pytest.raises(GraphCompatibilityError):
            loadGraph(graph.filepath, strictCompatibility=True)

    def test_loadsIfIncompatibleNodeHasDefaultAttributeValues(self, graphSavedOnDisk):
        with registeredNodeTypes([SampleNodeV1, SampleNodeV2]):
            graph: Graph = graphSavedOnDisk
            graph.addNewNode(SampleNodeV1.__name__)
            graph.save(template=True)

            replaceNodeTypeDesc(SampleNodeV1.__name__, SampleNodeV2)

            loadGraph(graph.filepath, strictCompatibility=True)

    def test_loadsIfValueSetOnCompatibleAttribute(self, graphSavedOnDisk):
        with registeredNodeTypes([SampleNodeV1, SampleNodeV2]):
            graph: Graph = graphSavedOnDisk
            node = graph.addNewNode(SampleNodeV1.__name__, paramA="foo")
            graph.save(template=True)

            replaceNodeTypeDesc(SampleNodeV1.__name__, SampleNodeV2)

            loadedGraph = loadGraph(graph.filepath, strictCompatibility=True)
            assert loadedGraph.nodes.get(node.name).paramA.value == "foo"

    def test_loadsIfValueSetOnIncompatibleAttribute(self, graphSavedOnDisk):
        with registeredNodeTypes([SampleNodeV1, SampleNodeV2]):
            graph: Graph = graphSavedOnDisk
            graph.addNewNode(SampleNodeV1.__name__, input="foo")
            graph.save(template=True)

            replaceNodeTypeDesc(SampleNodeV1.__name__, SampleNodeV2)

            loadGraph(graph.filepath, strictCompatibility=True)

class TestVersionConflict:

    def test_loadingConflictingNodeVersionCreatesCompatibilityNodes(self, graphSavedOnDisk):
        graph: Graph = graphSavedOnDisk

        with registeredNodeTypes([SampleNodeV1]):
            with overrideNodeTypeVersion(SampleNodeV1, "1.0"):
                node = graph.addNewNode(SampleNodeV1.__name__)
                graph.save()

            with overrideNodeTypeVersion(SampleNodeV1, "2.0"):
                otherGraph = Graph("")
                otherGraph.load(graph.filepath)

        assert len(otherGraph.compatibilityNodes) == 1
        assert otherGraph.node(node.name).issue is CompatibilityIssue.VersionConflict

    def test_loadingUnspecifiedNodeVersionAssumesCurrentVersion(self, graphSavedOnDisk):
        graph: Graph = graphSavedOnDisk

        with registeredNodeTypes([SampleNodeV1]):
            graph.addNewNode(SampleNodeV1.__name__)
            graph.save()

            with overrideNodeTypeVersion(SampleNodeV1, "2.0"):
                otherGraph = Graph("")
                otherGraph.load(graph.filepath)

        assert len(otherGraph.compatibilityNodes) == 0


class UidTestingNodeV1(desc.Node):
    inputs = [
        desc.File(name="input", label="Input", description="", value="", invalidate=True),
    ]
    outputs = [desc.File(name="output", label="Output",
                         description="", value="{nodeCacheFolder}")]


class UidTestingNodeV2(desc.Node):
    """ 
    Changes from SampleNodeBV1:
        * 'param' has been added
    """

    inputs = [
        desc.File(name="input", label="Input", description="", value="", invalidate=True),
        desc.ListAttribute(
            name="param",
            label="Param",
            elementDesc=desc.File(
                name="file",
                label="File",
                description="",
                value="",
            ),
            description="",
        ),
    ]
    outputs = [desc.File(name="output", label="Output", description="", value="{nodeCacheFolder}")]


class UidTestingNodeV3(desc.Node):
    """
    Changes from SampleNodeBV2:
        * 'input' is not invalidating the UID.
    """

    inputs = [
        desc.File(name="input", label="Input", description="", value="", invalidate=False),
        desc.ListAttribute(
            name="param",
            label="Param",
            elementDesc=desc.File(
                name="file",
                label="File",
                description="",
                value="",
            ),
            description="",
        ),
    ]
    outputs = [desc.File(name="output", label="Output",
                         description="", value="{nodeCacheFolder}")]


class TestUidConflict:
    def test_changingInvalidateOnAttributeDescCreatesUidConflict(self, graphSavedOnDisk):
        with registeredNodeTypes([UidTestingNodeV2]):
            graph: Graph = graphSavedOnDisk
            node = graph.addNewNode(UidTestingNodeV2.__name__)

            graph.save()
            replaceNodeTypeDesc(UidTestingNodeV2.__name__, UidTestingNodeV3)

            with pytest.raises(GraphCompatibilityError):
                loadGraph(graph.filepath, strictCompatibility=True)

            loadedGraph = loadGraph(graph.filepath)
            loadedNode = loadedGraph.node(node.name)
            assert isinstance(loadedNode, CompatibilityNode)
            assert loadedNode.issue == CompatibilityIssue.UidConflict

    def test_uidConflictingNodesPreserveConnectionsOnGraphLoad(self, graphSavedOnDisk):
        with registeredNodeTypes([UidTestingNodeV2]):
            graph: Graph = graphSavedOnDisk
            nodeA = graph.addNewNode(UidTestingNodeV2.__name__)
            nodeB = graph.addNewNode(UidTestingNodeV2.__name__)

            nodeB.param.append("")
            graph.addEdge(nodeA.output, nodeB.param.at(0))

            graph.save()
            replaceNodeTypeDesc(UidTestingNodeV2.__name__, UidTestingNodeV3)

            loadedGraph = loadGraph(graph.filepath)
            assert len(loadedGraph.compatibilityNodes) == 2

            loadedNodeA = loadedGraph.node(nodeA.name)
            loadedNodeB = loadedGraph.node(nodeB.name)

            assert loadedNodeB.param.at(0).linkParam == loadedNodeA.output

    def test_upgradingConflictingNodesPreserveConnections(self, graphSavedOnDisk):
        with registeredNodeTypes([UidTestingNodeV2]):
            graph: Graph = graphSavedOnDisk
            nodeA = graph.addNewNode(UidTestingNodeV2.__name__)
            nodeB = graph.addNewNode(UidTestingNodeV2.__name__)

            # Double-connect nodeA.output to nodeB, on both a single attribute and a list attribute
            nodeB.param.append("")
            graph.addEdge(nodeA.output, nodeB.param.at(0))
            graph.addEdge(nodeA.output, nodeB.input)

            graph.save()
            replaceNodeTypeDesc(UidTestingNodeV2.__name__, UidTestingNodeV3)

            def checkNodeAConnectionsToNodeB():
                loadedNodeA = loadedGraph.node(nodeA.name)
                loadedNodeB = loadedGraph.node(nodeB.name)
                return (
                    loadedNodeB.param.at(0).linkParam == loadedNodeA.output
                    and loadedNodeB.input.linkParam == loadedNodeA.output
                )

            loadedGraph = loadGraph(graph.filepath)
            loadedGraph.upgradeNode(nodeA.name)

            assert checkNodeAConnectionsToNodeB()
            loadedGraph.upgradeNode(nodeB.name)

            assert checkNodeAConnectionsToNodeB()
            assert len(loadedGraph.compatibilityNodes) == 0


    def test_uidConflictDoesNotPropagateToValidDownstreamNodeThroughConnection(
            self, graphSavedOnDisk):
        with registeredNodeTypes([UidTestingNodeV1, UidTestingNodeV2]):
            graph: Graph = graphSavedOnDisk
            nodeA = graph.addNewNode(UidTestingNodeV2.__name__)
            nodeB = graph.addNewNode(UidTestingNodeV1.__name__)

            graph.addEdge(nodeA.output, nodeB.input)

            graph.save()
            replaceNodeTypeDesc(UidTestingNodeV2.__name__, UidTestingNodeV3)

            loadedGraph = loadGraph(graph.filepath)
            assert len(loadedGraph.compatibilityNodes) == 1

    def test_uidConflictDoesNotPropagateToValidDownstreamNodeThroughListConnection(
            self,graphSavedOnDisk):
        with registeredNodeTypes([UidTestingNodeV2, UidTestingNodeV3]):
            graph: Graph = graphSavedOnDisk
            nodeA = graph.addNewNode(UidTestingNodeV2.__name__)
            nodeB = graph.addNewNode(UidTestingNodeV3.__name__)

            nodeB.param.append("")
            graph.addEdge(nodeA.output, nodeB.param.at(0))

            graph.save()
            replaceNodeTypeDesc(UidTestingNodeV2.__name__, UidTestingNodeV3)

            loadedGraph = loadGraph(graph.filepath)
            assert len(loadedGraph.compatibilityNodes) == 1
