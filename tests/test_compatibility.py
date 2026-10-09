#!/usr/bin/env python
# coding:utf-8
import tempfile
import os

import copy
from typing import Type
import pytest

from meshroom.core import desc, pluginManager
from meshroom.core.plugins.base import NodeDescProvider
from meshroom.core.exception import GraphCompatibilityError, NodeUpgradeError
from meshroom.core.graphIO import GraphSerializer
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
                                        description="", items=SampleGroupV1),
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
                                        description="", items=SampleGroupV1),
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
                               items=SampleGroupV1, name="gA", label="gA", description=""),
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
                               items=SampleGroupV2, name="gA", label="gA", description=""),
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
                               items=SampleGroupV3, name="gA", label="gA", description=""),
                           description="")
    ]
    outputs = [
        desc.File(name="output", label="Output", description="", value="{nodeCacheFolder}")
    ]


class SampleInitNodeV1(desc.InitNode):
    """ Version 1 Sample Init Node """
    inputs = [
        desc.StringParam(name="path", label="Path", description="",
                         value="", invalidate=False)  # No impact on UID
    ]
    outputs = [
        desc.File(name="output", label="Output", description="", value="{nodeCacheFolder}")
    ]


class SampleInitNodeV2(desc.InitNode):
    """
    Changes from V1:
        * 'path' has been renamed to 'in'
    """
    inputs = [
        desc.StringParam(name="in", label="path", description="",
                         value="", invalidate=False)  # No impact on UID
    ]
    outputs = [
        desc.File(name="output", label="Output", description="", value="{nodeCacheFolder}")
    ]


class OutputTemplateNodeV1(desc.Node):
    """ Node with an output File attribute pointing to a specific file. """
    inputs = [
        desc.File(name="input", label="Input", description="", value=""),
    ]
    outputs = [
        desc.File(name="output", label="Output", description="",
                  value="{nodeCacheFolder}/file.abc"),
    ]


class OutputTemplateNodeV2(desc.Node):
    """
    Changes from OutputTemplateNodeV1:
        * The output value template has changed from 'file.abc' to 'file.cba'.
    """
    inputs = [
        desc.File(name="input", label="Input", description="", value=""),
    ]
    outputs = [
        desc.File(name="output", label="Output", description="",
                  value="{nodeCacheFolder}/file.cba"),
    ]


def replaceNodeTypeDesc(nodeType: str, nodeDesc: Type[desc.Node]):
    """ Change the `nodeDesc` associated to `nodeType`. """
    pluginManager.getNodeDescProviders()[nodeType] = NodeDescProvider(nodeDesc)


def test_desc_only_node_node_type():
    """
    Test compatibility behavior for node type whose description is no longer available.
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
    assert n.issue == CompatibilityIssue.DescOnlyNodeType
    # Check if attributes are properly restored
    assert len(n.attributes) == 3
    assert n.input.isInput
    assert n.output.isOutput
    # Check if internal folder
    assert n.internalFolder == internalFolder

    # Upgrade cannot be performed on unknown node types
    assert not n.canUpgrade
    with pytest.raises(NodeUpgradeError):
        g.upgradeNode(nodeName)


def test_DescOnlyNodeType_preserves_types_uid_and_flow(tmp_path):
    """
    Test that param types, node UID and flow are preserved for node type whose description is no longer available.
    """
    graph = Graph("test")
    allAttrNode_1 = graph.addNewNode("AllAttributesNode", "allAttrNode_1")
    allAttrNode_2 = graph.addNewNode("AllAttributesNode", "allAttrNode_2")
    colorNode_1 = graph.addNewNode("Color", "colorNode_1")
    colorNode_2 = graph.addNewNode("Color", "colorNode_2")
    dynamicNode_1 = graph.addNewNode("DynamicNode", "dynamicNode_1")
    dynamicNode_2 = graph.addNewNode("DynamicNode", "dynamicNode_2")
    nestedGroupNode_1 = graph.addNewNode("GroupAttributes", "nestedGroupNode_1")
    nestedGroupNode_2 = graph.addNewNode("GroupAttributes", "nestedGroupNode_2")

    for v in colorNode_1.rgb.value.values():
        v.value = 1.1

    for v in colorNode_2.rgb.value.values():
        v.value = 1.2

    dynamicNode_1.code.value = "print('Hello from dynamicNode_1')"

    dynamicNode_1.ins.duplicateAttribute(colorNode_1.rgb)
    dynamicNode_1.ins.duplicateAttribute(colorNode_2.rgb)

    for v in dynamicNode_1.ins.rgb.value.values():
        v.value = 1.3

    dynamicNode_1.ins.duplicateAttribute(allAttrNode_1.stringParam)

    dynamicNode_2.outs.duplicateAttribute(dynamicNode_1.ins.rgb, isOutput=True)
    dynamicNode_1.outs.duplicateAttribute(colorNode_2.rgb, isOutput=True)

    dynamicNode_2.outs.rgb.connectTo(dynamicNode_1.ins.rgb)

    for v in dynamicNode_1.ins.rgb.value.values():
        v.value = 1.1

    allAttrNode_1.stringParam.value = "/some/path"
    dynamicNode_1.ins.stringParam.value = "/some/other/path"

    allAttrNode_1.keyableFloat.keyValues.add("0", 1.1)
    allAttrNode_1.keyableFloat.keyValues.add("1", 2.2)
    allAttrNode_1.keyableFloat.keyValues.add("12", 4.4)

    observationRectangle = {"center": {"x": 10, "y": 15}, "size": {"width": 20, "height": 25}}
    allAttrNode_1.keyableRectangle.geometry.setObservation("0", observationRectangle)
    allAttrNode_1.keyableRectangle.geometry.setObservation("1", observationRectangle)
    allAttrNode_1.keyableRectangle.geometry.setObservation("1", {"center": {"x": 30, "y": 35}})

    allAttrNode_1.internalAttribute("flowInputs").extend(["0","0","0"])
    allAttrNode_2.internalAttribute("flowInputs").extend(["0","0"])
    dynamicNode_2.internalAttribute("flowInputs").extend(["0","0"])
    nestedGroupNode_2.internalAttribute("flowInputs").append("0")

    graph.addEdge(colorNode_1.internalAttribute("flowOutput"), allAttrNode_1.internalAttribute("flowInputs").at(0))
    graph.addEdge(dynamicNode_1.internalAttribute("flowOutput"), allAttrNode_1.internalAttribute("flowInputs").at(1))
    graph.addEdge(nestedGroupNode_1.internalAttribute("flowOutput"), allAttrNode_1.internalAttribute("flowInputs").at(2))
    graph.addEdge(colorNode_2.internalAttribute("flowOutput"), allAttrNode_2.internalAttribute("flowInputs").at(0))
    graph.addEdge(dynamicNode_2.internalAttribute("flowOutput"), allAttrNode_2.internalAttribute("flowInputs").at(1))
    graph.addEdge(dynamicNode_1.internalAttribute("flowOutput"), dynamicNode_2.internalAttribute("flowInputs").at(0))
    graph.addEdge(nestedGroupNode_1.internalAttribute("flowOutput"), dynamicNode_2.internalAttribute("flowInputs").at(1))
    graph.addEdge(dynamicNode_2.internalAttribute("flowOutput"), nestedGroupNode_2.internalAttribute("flowInputs").at(0))

    # Check that flowInputs are links to flowOutputs
    assert all(att.isLink for att in allAttrNode_1.internalAttribute("flowInputs"))
    assert all(att.isLink for att in allAttrNode_2.internalAttribute("flowInputs"))
    assert all(att.isLink for att in dynamicNode_2.internalAttribute("flowInputs"))
    assert all(att.isLink for att in nestedGroupNode_2.internalAttribute("flowInputs"))

    allAttrNode_1_flowInputs = [att.getSerializedValue() for att in allAttrNode_1.internalAttribute("flowInputs")]
    allAttrNode_2_flowInputs = [att.getSerializedValue() for att in allAttrNode_2.internalAttribute("flowInputs")]
    dynamicNode_1_flowInputs = [att.getSerializedValue() for att in dynamicNode_1.internalAttribute("flowInputs")]
    nestedGroupNode_2_flowInputs = [att.getSerializedValue() for att in nestedGroupNode_2.internalAttribute("flowInputs")]

    # Change node type name to simulate missing description
    for node in graph.nodes:
        node._nodeType = node.nodeType + "_Missing"

    for node in graph.nodes:
        node._computeUid()

    node_names = [node.name for node in graph.nodes]
    node_uids = [node._uid for node in graph.nodes]

    nodeDescriptions = GraphSerializer(graph).serializeNodeDescriptions()
    serializedGraph = GraphSerializer(graph).serializeContent()

    graphFile = os.path.join(tmp_path, "test_desc_only_node_type.mg")
    graph.save(graphFile)

    # Reload graph with only compatibilityNodes
    graph = loadGraph(graphFile)

    allAttrNode_1_ = graph.node("allAttrNode_1")
    allAttrNode_2_ = graph.node("allAttrNode_2")
    dynamicNode_1_ = graph.node("dynamicNode_1")
    nestedGroupNode_2_ = graph.node("nestedGroupNode_2")

    allAttrNode_1_flowInputs_ = [att.getSerializedValue() for att in allAttrNode_1_.internalAttribute("flowInputs")]
    allAttrNode_2_flowInputs_ = [att.getSerializedValue() for att in allAttrNode_2_.internalAttribute("flowInputs")]
    dynamicNode_1_flowInputs_ = [att.getSerializedValue() for att in dynamicNode_1_.internalAttribute("flowInputs")]
    nestedGroupNode_2_flowInputs_ = [att.getSerializedValue() for att in nestedGroupNode_2_.internalAttribute("flowInputs")]

    # Check that flowInputs are preserved after reloading the graph with only CompatibilityNodes
    assert allAttrNode_1_flowInputs_ == allAttrNode_1_flowInputs
    assert allAttrNode_2_flowInputs_ == allAttrNode_2_flowInputs
    assert dynamicNode_1_flowInputs_ == dynamicNode_1_flowInputs
    assert nestedGroupNode_2_flowInputs_ == nestedGroupNode_2_flowInputs

    for node in graph.nodes:
        node._computeUid()

    for node_name, uid in zip(node_names, node_uids):
        node = graph.node(node_name)
        # Check that all nodes are DescOnlyNodeType CompatibilityNodes
        assert isinstance(node, CompatibilityNode)
        assert node.issue == CompatibilityIssue.DescOnlyNodeType
        # Check UID is preserved
        assert node._uid == uid

    graphFile = os.path.join(tmp_path, "test_desc_only_node_type_.mg")
    nodeDescriptions_ = GraphSerializer(graph).serializeNodeDescriptions()
    serializedGraph_ = GraphSerializer(graph).serializeContent()

    # Check that the loaded graph is identical to the original one
    # (i.e. attribute types, node UID and flow have been successfully preserved)
    assert nodeDescriptions_ == nodeDescriptions
    assert serializedGraph_ == serializedGraph

    # Check that the loaded graph can be successfully edited
    allAttrNode_1_.keyableFloat.keyValues.add("8", 8.8)
    allAttrNode_1_.keyableRectangle.geometry.setObservation("2", observationRectangle)
    allAttrNode_1_.keyableRectangle.geometry.setObservation("2", {"size": {"width": 40, "height": 45}})

    serializedGraph_ = GraphSerializer(graph).serializeContent()
    assert serializedGraph_ != serializedGraph


def test_description_conflict():
    """
    Test compatibility behavior for conflicting node descriptions.
    """
    # Copy registered node types to be able to restore them
    originalNodeTypes = copy.deepcopy(pluginManager.getNodeDescProviders())

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
        pluginManager.getNodeDescProviders()[nt.__name__] = NodeDescProvider(nodeTypes[i + 1])

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
            # Flow attributes are now in internalAttributes
            assert upgradedNode.hasInternalAttribute("flowInputs")
            assert upgradedNode.hasInternalAttribute("flowOutput")
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
            assert isinstance(upgradedNode.paramA.desc, desc.ListAttribute)
            # paramA child attributes invalidate UID
            assert upgradedNode.internalFolder != srcNode.internalFolder

        elif isinstance(srcNode.nodeDesc, SampleNodeV4):
            # V4 => V5: 'paramA' elementDesc has changed from SampleGroupV1 to SampleGroupV2
            assert len(compatNode.attributes) == 3
            assert hasattr(compatNode, "paramA")
            groupAttribute = compatNode.paramA.desc.elementDesc

            assert isinstance(groupAttribute, desc.GroupAttribute)
            # Check that Compatibility node respect SampleGroupV1 description
            for elt in groupAttribute.items:
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
    pluginManager._nodeDescProviders = originalNodeTypes


def test_upgradeAllNodes(tmp_path):
    registerNodeDesc(SampleNodeV1)
    registerNodeDesc(SampleNodeV2)
    registerNodeDesc(SampleInitNodeV1)
    registerNodeDesc(SampleInitNodeV2)

    g = Graph("")
    n1 = g.addNewNode("SampleNodeV1")
    n2 = g.addNewNode("SampleNodeV2")
    n3 = g.addNewNode("SampleInitNodeV1")
    n4 = g.addNewNode("SampleInitNodeV2")
    n1Name = n1.name
    n2Name = n2.name
    n3Name = n3.name
    n4Name = n4.name
    graphFile = os.path.join(tmp_path, "test_description_conflict.mg")
    g.save(graphFile)

    # Replace SampleNodeV1 by SampleNodeV2 and SampleInitNodeV1 by SampleInitNodeV2
    pluginManager.getNodeDescProviders()[SampleNodeV1.__name__] = \
        pluginManager.getNodeDescProvider(SampleNodeV2.__name__)
    pluginManager.getNodeDescProviders()[SampleInitNodeV1.__name__] = \
        pluginManager.getNodeDescProvider(SampleInitNodeV2.__name__)
    # Make SampleNodeV2 and SampleInitNodeV2 an unknown type
    unregisterNodeDesc(SampleNodeV2)
    unregisterNodeDesc(SampleInitNodeV2)

    # Reload file
    g = loadGraph(graphFile)
    os.remove(graphFile)

    # Both nodes are CompatibilityNodes
    assert len(g.compatibilityNodes) == 4
    assert g.node(n1Name).canUpgrade      # description conflict
    assert g.node(n3Name).canUpgrade      # description conflict
    assert not g.node(n2Name).canUpgrade  # unknown type
    assert not g.node(n4Name).canUpgrade  # unknown type

    # Upgrade all upgradable nodes
    g.upgradeAllNodes()

    # Only the nodes with an unknown type have not been upgraded
    assert len(g.compatibilityNodes) == 2
    assert n2Name in g.compatibilityNodes.keys()
    assert n4Name in g.compatibilityNodes.keys()

    unregisterNodeDesc(SampleNodeV1)
    unregisterNodeDesc(SampleInitNodeV1)


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
    pluginManager.getNodeDescProviders()[SampleNodeV5.__name__] = \
        pluginManager.getNodeDescProvider(SampleNodeV6.__name__)

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


def test_outputValueAfterDefaultOutputChange(tmp_path):
    """
    Test that when the default value of a node's output attribute is changed in the node
    description, a saved graph that is reopened preserves the values saved on disk.

    A new instance of that node is then created to check that the new default value is
    properly applied to new nodes.
    """
    registerNodeDesc(OutputTemplateNodeV1)

    g = Graph("")
    n = g.addNewNode(OutputTemplateNodeV1.__name__)
    nodeName = n.name
    assert n.output.value.endswith("/file.abc")

    graphFile = os.path.join(tmp_path, "test_output_value_change.mg")
    g.save(graphFile)

    # Replace the registered description with V2 (only the output value changes)
    replaceNodeTypeDesc(OutputTemplateNodeV1.__name__, OutputTemplateNodeV2)

    # Reload the graph with the updated description
    reloadedGraph = loadGraph(graphFile)
    reloadedNode = reloadedGraph.node(nodeName)

    # The reloaded node should not be a CompatibilityNode
    assert not isinstance(reloadedNode, CompatibilityNode)

    # The reloaded node should reflect the value saved on disk, not the new default value in the description
    assert not reloadedNode.output.value.endswith("/file.cba")

    # The internal folder (driven by inputs, not outputs) must be unchanged
    assert reloadedNode.internalFolder == n.internalFolder

    # A new instance of this node should reflect the new default value in the description
    n = g.addNewNode(OutputTemplateNodeV1.__name__)
    assert n.output.value.endswith("/file.cba")

    unregisterNodeDesc(OutputTemplateNodeV1)


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

    def test_loadingUnspecifiedNodeVersionCreatesCompatibilityNodes(self, graphSavedOnDisk):
        graph: Graph = graphSavedOnDisk

        with registeredNodeTypes([SampleNodeV1]):
            node = graph.addNewNode(SampleNodeV1.__name__)
            graph.save()

            with overrideNodeTypeVersion(SampleNodeV1, "2.0"):
                otherGraph = Graph("")
                otherGraph.load(graph.filepath)

        assert len(otherGraph.compatibilityNodes) == 1
        assert otherGraph.node(node.name).issue is CompatibilityIssue.VersionConflict

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
            nodeA.output.connectTo(nodeB.param.at(0))

            graph.save()
            replaceNodeTypeDesc(UidTestingNodeV2.__name__, UidTestingNodeV3)

            loadedGraph = loadGraph(graph.filepath)
            assert len(loadedGraph.compatibilityNodes) == 2

            loadedNodeA = loadedGraph.node(nodeA.name)
            loadedNodeB = loadedGraph.node(nodeB.name)

            assert loadedNodeB.param.at(0).inputLink == loadedNodeA.output

    def test_upgradingConflictingNodesPreserveConnections(self, graphSavedOnDisk):
        with registeredNodeTypes([UidTestingNodeV2]):
            graph: Graph = graphSavedOnDisk
            nodeA = graph.addNewNode(UidTestingNodeV2.__name__)
            nodeB = graph.addNewNode(UidTestingNodeV2.__name__)

            # Double-connect nodeA.output to nodeB, on both a single attribute and a list attribute
            nodeB.param.append("")
            nodeA.output.connectTo(nodeB.param.at(0))
            nodeA.output.connectTo(nodeB.input)

            graph.save()
            replaceNodeTypeDesc(UidTestingNodeV2.__name__, UidTestingNodeV3)

            def checkNodeAConnectionsToNodeB():
                loadedNodeA = loadedGraph.node(nodeA.name)
                loadedNodeB = loadedGraph.node(nodeB.name)
                return (
                    loadedNodeB.param.at(0).inputLink == loadedNodeA.output
                    and loadedNodeB.input.inputLink == loadedNodeA.output
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

            nodeA.output.connectTo(nodeB.input)

            graph.save()
            replaceNodeTypeDesc(UidTestingNodeV2.__name__, UidTestingNodeV3)

            loadedGraph = loadGraph(graph.filepath)
            assert len(loadedGraph.compatibilityNodes) == 1

    def test_uidConflictDoesNotPropagateToValidDownstreamNodeThroughListConnection(
            self, graphSavedOnDisk):
        with registeredNodeTypes([UidTestingNodeV2, UidTestingNodeV3]):
            graph: Graph = graphSavedOnDisk
            nodeA = graph.addNewNode(UidTestingNodeV2.__name__)
            nodeB = graph.addNewNode(UidTestingNodeV3.__name__)

            nodeB.param.append("")
            nodeA.output.connectTo(nodeB.param.at(0))

            graph.save()
            replaceNodeTypeDesc(UidTestingNodeV2.__name__, UidTestingNodeV3)

            loadedGraph = loadGraph(graph.filepath)
            assert len(loadedGraph.compatibilityNodes) == 1
