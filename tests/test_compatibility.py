#!/usr/bin/env python
# coding:utf-8
import tempfile
import os

import copy
import json
from typing import Type
import pytest

from meshroom.core import desc, pluginManager
from meshroom.core.attribute import AnySet
from meshroom.core.desc.validators import NotEmptyValidator
from meshroom.core.plugins.base import NodeDescProvider
from meshroom.core.exception import GraphCompatibilityError, NodeUpgradeError
from meshroom.core.graphIO import GraphIO, GraphSerializer
from meshroom.core.graph import Graph, loadGraph
from meshroom.core.node import CompatibilityNode, CompatibilityIssue, Node, Status
from meshroom.core.nodeFactory import nodeFactory

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


def simulateMissingNodeTypes(graphFile: str, nodeNames: list, keepNodeDescriptions: bool = True):
    """
    Rename the node type of the given nodes in a saved graph file, so that their node type
    is not registered anymore when the file is loaded.

    Args:
        graphFile: The path of the saved graph file to modify.
        nodeNames: The names of the nodes whose node type should be missing.
        keepNodeDescriptions: Whether the serialized node descriptions should be kept in the file (DescOnlyNodeType)
                              or removed to simulate a file saved without them (UnknownNodeType).
    """
    with open(graphFile) as f:
        graphData = json.load(f)

    nodeDescriptions = graphData.get(GraphIO.Keys.NodeDescriptions, {})
    for nodeName in nodeNames:
        nodeData = graphData[GraphIO.Keys.Graph][nodeName]
        nodeType = nodeData["nodeType"]
        nodeData["nodeType"] = f"{nodeType}_Missing"
        if nodeType in nodeDescriptions:
            nodeDescriptions[f"{nodeType}_Missing"] = nodeDescriptions.pop(nodeType)

    if not keepNodeDescriptions:
        graphData.pop(GraphIO.Keys.NodeDescriptions, None)

    with open(graphFile, "w") as f:
        json.dump(graphData, f)


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


def test_unknownNodeTypeWithAnysetLoadsWithoutNodeDescriptions(tmp_path):
    """
    Test that a graph containing an unknown node type with an AnySet holding children of different types
    can be loaded when the node descriptions are not serialized in the .mg file (i.e. files saved before
    node descriptions were serialized), and that the AnySet children and their values are preserved.
    """
    graph = Graph("test")
    allAttrNode = graph.addNewNode("AllAttributesNode")
    dynamicNode = graph.addNewNode("DynamicNode")
    lsNode = graph.addNewNode("Ls")

    # The AnySet children have different types: inferring the type of all the children from the first one fails
    dynamicNode.ins.duplicateAttribute(allAttrNode.stringParam)
    dynamicNode.ins.duplicateAttribute(allAttrNode.intParam)
    dynamicNode.ins.duplicateAttribute(allAttrNode.boolParam)
    dynamicNode.ins.duplicateAttribute(allAttrNode.floatParam)
    dynamicNode.ins.stringParam.value = "someString"
    dynamicNode.ins.intParam.value = 11
    dynamicNode.ins.boolParam.value = True
    dynamicNode.ins.floatParam.value = 0.5
    dynamicNode.outs.duplicateAttribute(lsNode.input, isOutput=True)
    dynamicNode.outs.input.connectTo(lsNode.input)

    expectedInsChildren = [(child.name, child.desc.type, child.value) for child in dynamicNode.ins.value]
    assert len({childType for _, childType, _ in expectedInsChildren}) == 4

    graphFile = os.path.join(tmp_path, "test_unknown_node_type_anyset.mg")
    graph.save(graphFile)

    # Simulate an unknown node type in a file saved without the node descriptions
    with open(graphFile) as f:
        graphData = json.load(f)
    graphData.pop(GraphIO.Keys.NodeDescriptions, None)
    graphData[GraphIO.Keys.Graph][dynamicNode.name]["nodeType"] = "DynamicNode_Missing"
    serializedNode = copy.deepcopy(graphData[GraphIO.Keys.Graph][dynamicNode.name])
    with open(graphFile, "w") as f:
        json.dump(graphData, f)

    graph = loadGraph(graphFile)

    node = graph.node(dynamicNode.name)
    assert isinstance(node, CompatibilityNode)
    # No node description has been serialized: the node type is fully unknown
    assert node.issue == CompatibilityIssue.UnknownNodeType
    assert not node.canUpgrade

    # Check that the AnySet and its children have been restored with their own types and values
    assert isinstance(node.ins, AnySet)
    assert [(child.name, child.desc.type, child.value) for child in node.ins.value] == expectedInsChildren
    assert isinstance(node.outs, AnySet)
    assert [child.name for child in node.outs.value] == ["input"]

    # Check that the edge from the AnySet's child is restored
    assert graph.node(lsNode.name).input.isLink

    # Check that the AnySets are serialized back identically
    nodeDict = node.toDict()
    assert nodeDict["inputs"]["ins"] == serializedNode["inputs"]["ins"]
    assert nodeDict["outputs"]["outs"] == serializedNode["outputs"]["outs"]


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

    def test_loadsDescOnlyNodeTypes(self, graphSavedOnDisk):
        """
        Templates do not serialize outputs nor inputs with default values: these attributes must be
        created from the serialized node descriptions, including GroupAttributes and AnySets.
        """
        graph: Graph = graphSavedOnDisk
        allAttrNode = graph.addNewNode("AllAttributesNode")
        dynamicNode = graph.addNewNode("DynamicNode")
        groupNode = graph.addNewNode("GroupAttributes")

        dynamicNode.ins.duplicateAttribute(allAttrNode.stringParam)
        dynamicNode.ins.duplicateAttribute(allAttrNode.intParam)
        dynamicNode.ins.stringParam.value = "someString"
        dynamicNode.ins.intParam.value = 11
        expectedInsChildren = [(child.name, child.desc.type, child.value) for child in dynamicNode.ins.value]

        graph.save(template=True)
        simulateMissingNodeTypes(graph.filepath, [dynamicNode.name, groupNode.name])

        loadedGraph = loadGraph(graph.filepath)

        loadedDynamicNode = loadedGraph.node(dynamicNode.name)
        assert isinstance(loadedDynamicNode, CompatibilityNode)
        assert loadedDynamicNode.issue == CompatibilityIssue.DescOnlyNodeType
        # Non-default AnySet input serialized in the template
        assert [(child.name, child.desc.type, child.value)
                for child in loadedDynamicNode.ins.value] == expectedInsChildren
        # Default input and AnySet output, only available through the node description
        assert loadedDynamicNode.hasAttribute("code")
        assert isinstance(loadedDynamicNode.outs, AnySet)

        loadedGroupNode = loadedGraph.node(groupNode.name)
        assert isinstance(loadedGroupNode, CompatibilityNode)
        assert loadedGroupNode.issue == CompatibilityIssue.DescOnlyNodeType
        # Default GroupAttribute input and GroupAttribute output, only available through the node description
        assert loadedGroupNode.hasAttribute("firstGroup")
        assert loadedGroupNode.hasAttribute("outputGroup")

    def test_loadsUnknownNodeTypeWithAnySet(self, graphSavedOnDisk):
        """ A template saved without node descriptions can be loaded with an AnySet holding children of different types. """
        graph: Graph = graphSavedOnDisk
        allAttrNode = graph.addNewNode("AllAttributesNode")
        dynamicNode = graph.addNewNode("DynamicNode")

        dynamicNode.ins.duplicateAttribute(allAttrNode.stringParam)
        dynamicNode.ins.duplicateAttribute(allAttrNode.intParam)
        dynamicNode.ins.duplicateAttribute(allAttrNode.boolParam)
        dynamicNode.ins.stringParam.value = "someString"
        dynamicNode.ins.intParam.value = 11
        dynamicNode.ins.boolParam.value = True
        expectedInsChildren = [(child.name, child.desc.type, child.value) for child in dynamicNode.ins.value]

        graph.save(template=True)
        simulateMissingNodeTypes(graph.filepath, [dynamicNode.name], keepNodeDescriptions=False)

        loadedGraph = loadGraph(graph.filepath)

        loadedDynamicNode = loadedGraph.node(dynamicNode.name)
        assert isinstance(loadedDynamicNode, CompatibilityNode)
        assert loadedDynamicNode.issue == CompatibilityIssue.UnknownNodeType
        assert [(child.name, child.desc.type, child.value)
                for child in loadedDynamicNode.ins.value] == expectedInsChildren

    def test_nodeWithoutVersionIsUpgraded(self, graphSavedOnDisk):
        """
        A node saved in a template without any version information is considered to be in version "0.0":
        if its node type is versioned, it conflicts with it and is automatically upgraded, keeping its values.
        """
        with registeredNodeTypes([SampleNodeV1]):
            graph: Graph = graphSavedOnDisk
            node = graph.addNewNode(SampleNodeV1.__name__, paramA="foo")
            graph.save(template=True)

            # Simulate a template saved without any version information for the node
            with open(graph.filepath) as f:
                graphData = json.load(f)
            graphData[GraphIO.Keys.Graph][node.name].pop("version", None)
            graphData[GraphIO.Keys.Header].pop(GraphIO.Keys.NodesVersions, None)
            with open(graph.filepath, "w") as f:
                json.dump(graphData, f)

            with overrideNodeTypeVersion(SampleNodeV1, "2.0"):
                loadedGraph = loadGraph(graph.filepath)

        loadedNode = loadedGraph.node(node.name)
        assert isinstance(loadedNode, Node)
        assert loadedNode.paramA.value == "foo"


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

    def test_uidConflictingNodesPreserveFlowConnectionsOnGraphLoad(self, graphSavedOnDisk):
        with registeredNodeTypes([UidTestingNodeV2]):
            graph: Graph = graphSavedOnDisk
            nodeA = graph.addNewNode(UidTestingNodeV2.__name__)
            nodeB = graph.addNewNode(UidTestingNodeV2.__name__)

            nodeB.internalAttribute("flowInputs").append("0")
            graph.addEdge(nodeA.internalAttribute("flowOutput"), nodeB.internalAttribute("flowInputs").at(0))

            graph.save()
            replaceNodeTypeDesc(UidTestingNodeV2.__name__, UidTestingNodeV3)

            # UID conflicting nodes are recreated without their node description
            loadedGraph = loadGraph(graph.filepath)
            assert len(loadedGraph.compatibilityNodes) == 2

            loadedNodeA = loadedGraph.node(nodeA.name)
            loadedNodeB = loadedGraph.node(nodeB.name)

            flowInput = loadedNodeB.internalAttribute("flowInputs").at(0)
            assert flowInput.inputLink == loadedNodeA.internalAttribute("flowOutput")

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


class ValidatedNodeV1(desc.Node):
    """ Node with a mandatory input, validated by a NotEmptyValidator. """
    inputs = [
        desc.StringParam(name="value", label="Value", description="", value="",
                         validators=[NotEmptyValidator()]),
    ]
    outputs = [
        desc.File(name="output", label="Output", description="", value="{nodeCacheFolder}"),
    ]


class ValidatedNodeV2(desc.Node):
    """
    Changes from V1:
        * 'extra' has been added, which makes V1 serialized data a description conflict.
          'value' still matches, so the CompatibilityNode keeps the validator.
    """
    inputs = [
        desc.StringParam(name="value", label="Value", description="", value="",
                         validators=[NotEmptyValidator()]),
        desc.StringParam(name="extra", label="Extra", description="", value="", invalidate=False),
    ]
    outputs = [
        desc.File(name="output", label="Output", description="", value="{nodeCacheFolder}"),
    ]


class TestCompatibilityNodeNotifications:
    """ Status and validation changes of a CompatibilityNode must be notified to the listeners (e.g. the UI). """

    @staticmethod
    def writeNodeStatus(node, status="SUCCESS"):
        """ Write a nodeStatus file in the internal folder of `node`. """
        os.makedirs(node.internalFolder, exist_ok=True)
        with open(os.path.join(node.internalFolder, "nodeStatus"), "w") as f:
            json.dump({"nodeName": node.name, "status": status, "execMode": "LOCAL"}, f)

    @pytest.fixture
    def compatibilityGraph(self, tmp_path):
        """
        Yield a (graph, nodeName) tuple where the graph has been reloaded from a file and
        contains one CompatibilityNode (description conflict) that can be upgraded.
        """
        with registeredNodeTypes([ValidatedNodeV1, ValidatedNodeV2]):
            graph = Graph("")
            nodeName = graph.addNewNode(ValidatedNodeV1.__name__).name
            graphFile = str(tmp_path / "test_compatibility_node.mg")
            graph.save(graphFile)

            # ValidatedNodeV1 now refers to the V2 description
            replaceNodeTypeDesc(ValidatedNodeV1.__name__, ValidatedNodeV2)
            yield loadGraph(graphFile), nodeName

    def test_updateStatusFromCacheEmitsGlobalStatusChanged(self, compatibilityGraph):
        """ A status loaded from the cache must be notified, as the node chunks are not connected. """
        graph, nodeName = compatibilityGraph
        node = graph.node(nodeName)
        assert isinstance(node, CompatibilityNode)
        assert node.issue == CompatibilityIssue.DescriptionConflict
        assert node.getGlobalStatus() == Status.NONE

        emitted = []
        node.globalStatusChanged.connect(lambda: emitted.append(node.getGlobalStatus()))

        self.writeNodeStatus(node, "SUCCESS")
        node.updateStatusFromCache()

        assert node.getGlobalStatus() == Status.SUCCESS
        assert emitted == [Status.SUCCESS]

        # Status has not changed: no new notification
        node.updateStatusFromCache()
        assert emitted == [Status.SUCCESS]

        # Status file removed: back to NONE, and notified
        os.remove(os.path.join(node.internalFolder, "nodeStatus"))
        node.updateStatusFromCache()
        assert node.getGlobalStatus() == Status.NONE
        assert emitted == [Status.SUCCESS, Status.NONE]

    def test_updateStatusFromCacheEmitsHasInvalidAttributeChanged(self, compatibilityGraph):
        """ The validation state must be notified, as _onAttributeChanged ignores CompatibilityNodes. """
        graph, nodeName = compatibilityGraph
        node = graph.node(nodeName)
        assert isinstance(node, CompatibilityNode)
        # The validator of the current description is kept on the CompatibilityNode attribute
        assert node._hasInvalidAttribute()

        emitted = []
        node.hasInvalidAttributeChanged.connect(lambda: emitted.append(True))
        node.updateStatusFromCache()
        assert len(emitted) == 1

    def test_replaceNodeNotifiesStatusAndValidation(self, compatibilityGraph):
        """
        Upgrade a CompatibilityNode and recreate it as the undo of the upgrade does:
        the restored node is added to a live graph, and its status and validation must be notified.
        """
        graph, nodeName = compatibilityGraph
        compatNode = graph.node(nodeName)
        self.writeNodeStatus(compatNode, "SUCCESS")
        nodeDict = copy.deepcopy(compatNode.toDict())

        upgradedNode = graph.upgradeNode(nodeName)
        assert isinstance(upgradedNode, Node)

        restoredNode = nodeFactory(nodeDict, name=nodeName)
        assert isinstance(restoredNode, CompatibilityNode)

        statusEmitted = []
        validationEmitted = []
        restoredNode.globalStatusChanged.connect(lambda: statusEmitted.append(True))
        restoredNode.hasInvalidAttributeChanged.connect(lambda: validationEmitted.append(True))

        graph.replaceNode(nodeName, restoredNode)

        assert graph.node(nodeName) is restoredNode
        assert restoredNode.internalFolder == compatNode.internalFolder
        assert restoredNode.getGlobalStatus() == Status.SUCCESS
        assert statusEmitted
        assert validationEmitted
        assert restoredNode._hasInvalidAttribute()


class ConnectedNodeV1(desc.Node):
    """ Node with a File input, a list of Files, and two outputs. """
    inputs = [
        desc.File(name="input", label="Input", description="", value=""),
        desc.ListAttribute(
            name="files", label="Files", description="",
            elementDesc=desc.File(name="file", label="File", description="", value=""),
        ),
    ]
    outputs = [
        desc.File(name="output", label="Output", description="", value="{nodeCacheFolder}"),
        desc.File(name="removedOutput", label="Removed Output", description="",
                  value="{nodeCacheFolder}/removed"),
    ]


class ConnectedNodeV2(desc.Node):
    """
    Changes from V1:
        * 'extra' has been added (description conflict): every connection can be restored on upgrade.
    """
    inputs = [
        desc.File(name="input", label="Input", description="", value=""),
        desc.ListAttribute(
            name="files", label="Files", description="",
            elementDesc=desc.File(name="file", label="File", description="", value=""),
        ),
        desc.StringParam(name="extra", label="Extra", description="", value="", invalidate=False),
    ]
    outputs = [
        desc.File(name="output", label="Output", description="", value="{nodeCacheFolder}"),
        desc.File(name="removedOutput", label="Removed Output", description="",
                  value="{nodeCacheFolder}/removed"),
    ]


class ConnectedNodeV3(desc.Node):
    """
    Changes from V1:
        * 'removedOutput' has been removed: connections starting from it cannot be restored on upgrade.
    """
    inputs = [
        desc.File(name="input", label="Input", description="", value=""),
        desc.ListAttribute(
            name="files", label="Files", description="",
            elementDesc=desc.File(name="file", label="File", description="", value=""),
        ),
    ]
    outputs = [
        desc.File(name="output", label="Output", description="", value="{nodeCacheFolder}"),
    ]


class TestUpgradeConnections:
    """ Upgrading a CompatibilityNode, and the equivalent of undoing the upgrade, must preserve all the connections. """

    @pytest.fixture
    def connectedGraphFactory(self, tmp_path):
        """
        Yield a function that creates a graph "up -> mid -> down", saves it, replaces the description of
        the "mid" node type with the given one and reloads the graph (making "mid" a CompatibilityNode).
        The function returns the (graph, midNodeName) tuple.
        """
        nodeDescs = [UidTestingNodeV1, UidTestingNodeV3, ConnectedNodeV1, ConnectedNodeV2, ConnectedNodeV3]
        with registeredNodeTypes(nodeDescs):
            def create(targetDesc):
                graph = Graph("")
                up = graph.addNewNode(UidTestingNodeV1.__name__)
                mid = graph.addNewNode(ConnectedNodeV1.__name__)
                down = graph.addNewNode(UidTestingNodeV3.__name__)

                # Connections arriving to "mid": on a simple attribute, and on a list element
                mid.files.append("")
                up.output.connectTo(mid.input)
                up.output.connectTo(mid.files.at(0))

                # Connections starting from "mid": on simple attribute, and on list elements
                down.param.append("")
                down.param.append("")
                mid.output.connectTo(down.input)
                mid.output.connectTo(down.param.at(0))
                mid.removedOutput.connectTo(down.param.at(1))

                # Flow connections arriving to and starting from "mid"
                mid.internalAttribute("flowInputs").append("0")
                down.internalAttribute("flowInputs").append("0")
                graph.addEdge(up.internalAttribute("flowOutput"), mid.internalAttribute("flowInputs").at(0))
                graph.addEdge(mid.internalAttribute("flowOutput"), down.internalAttribute("flowInputs").at(0))

                graphFile = str(tmp_path / "test_connected_graph.mg")
                graph.save(graphFile)

                replaceNodeTypeDesc(ConnectedNodeV1.__name__, targetDesc)
                return loadGraph(graphFile), mid.name

            yield create

    @staticmethod
    def edgeNames(graph):
        """ Return the set of (srcFullName, dstFullName) for all the edges of `graph`. """
        return {(edge.src.fullName, edge.dst.fullName) for edge in graph.edges}

    @staticmethod
    def upgrade(graph, nodeName):
        """
        Upgrade the CompatibilityNode `nodeName` and return what is needed to undo the upgrade.
        Mirrors the redo of the UpgradeNodeCommand (UI): the CompatibilityNode is serialized
        beforehand, along with its issue and its node description, and the outgoing edges that
        are removed with it are kept.
        """
        node = graph.node(nodeName)
        nodeDict = copy.deepcopy(node.toDict())
        nodeDescDict = copy.deepcopy(node.nodeDescDict)
        outEdges, outListAttributes = graph.replaceNode(nodeName, node.upgrade())
        return nodeDict, nodeDescDict, node.issue, outEdges, outListAttributes

    @staticmethod
    def undoUpgrade(graph, nodeName, snapshot):
        """
        Recreate the CompatibilityNode `nodeName` in place of the upgraded node.
        Mirrors the undo of the UpgradeNodeCommand (UI).
        """
        nodeDict, nodeDescDict, issue, outEdges, outListAttributes = snapshot
        expectedUid = graph.node(nodeName)._uid if issue == CompatibilityIssue.UidConflict else None
        restoredNode = nodeFactory(nodeDict, name=nodeName, expectedUid=expectedUid, nodeDescDict=nodeDescDict)
        graph.replaceNode(nodeName, restoredNode, outEdges, outListAttributes)

    def test_upgradePreservesConnections(self, connectedGraphFactory):
        graph, nodeName = connectedGraphFactory(ConnectedNodeV2)
        assert isinstance(graph.node(nodeName), CompatibilityNode)
        edgesBefore = self.edgeNames(graph)
        # 2 incoming + 3 outgoing + 2 flow connections
        assert len(edgesBefore) == 7

        self.upgrade(graph, nodeName)

        assert isinstance(graph.node(nodeName), Node)
        assert self.edgeNames(graph) == edgesBefore

    def test_recreatingCompatibilityNodeWithoutNodeDescriptionPreservesConnections(self, connectedGraphFactory):
        """
        Mirrors the undo of the RemoveNodeCommand (UI), which recreates the CompatibilityNode
        from its serialized data only, without its node description.
        """
        graph, nodeName = connectedGraphFactory(ConnectedNodeV2)
        edgesBefore = self.edgeNames(graph)

        nodeDict = copy.deepcopy(graph.node(nodeName).toDict())
        _, outEdges, outListAttributes = graph.removeNode(nodeName)
        graph.addNode(nodeFactory(nodeDict, nodeName), nodeName)
        graph._restoreOutEdges(outEdges, outListAttributes)

        assert isinstance(graph.node(nodeName), CompatibilityNode)
        assert self.edgeNames(graph) == edgesBefore

    def test_compatibilityNodeSerializesUpdatedFlowConnections(self, connectedGraphFactory, tmp_path):
        graph, nodeName = connectedGraphFactory(ConnectedNodeV2)
        flowInputs = graph.node(nodeName).internalAttribute("flowInputs")
        upNode = flowInputs.at(0).inputLink.node

        # Rename the upstream node: its previous name is then taken by a new node, connected with a new flow edge
        graph.renameNode(upNode, "renamedUp")
        newUpNode = graph.addNewNode(UidTestingNodeV1.__name__)
        flowInputs.append("0")
        graph.addEdge(newUpNode.internalAttribute("flowOutput"), flowInputs.at(1))
        edgesBefore = self.edgeNames(graph)

        graphFile = str(tmp_path / "test_updated_graph.mg")
        graph.save(graphFile)
        loadedGraph = loadGraph(graphFile)

        assert isinstance(loadedGraph.node(nodeName), CompatibilityNode)
        assert self.edgeNames(loadedGraph) == edgesBefore

    def test_compatibilityNodeSerializesRemovedFlowConnections(self, connectedGraphFactory, tmp_path):
        graph, nodeName = connectedGraphFactory(ConnectedNodeV2)
        flowInputs = graph.node(nodeName).internalAttribute("flowInputs")
        graph.removeEdge(flowInputs.at(0))
        flowInputs.remove(0)
        edgesBefore = self.edgeNames(graph)

        graphFile = str(tmp_path / "test_updated_graph.mg")
        graph.save(graphFile)
        loadedGraph = loadGraph(graphFile)

        assert len(loadedGraph.node(nodeName).internalAttribute("flowInputs")) == 0
        assert self.edgeNames(loadedGraph) == edgesBefore

    def test_undoUpgradeRestoresCompatibilityNodeAndConnections(self, connectedGraphFactory):
        graph, nodeName = connectedGraphFactory(ConnectedNodeV2)
        edgesBefore = self.edgeNames(graph)

        snapshot = self.upgrade(graph, nodeName)
        assert isinstance(graph.node(nodeName), Node)

        self.undoUpgrade(graph, nodeName, snapshot)

        assert isinstance(graph.node(nodeName), CompatibilityNode)
        assert self.edgeNames(graph) == edgesBefore

    def test_repeatedUpgradeAndUndoPreserveConnections(self, connectedGraphFactory):
        graph, nodeName = connectedGraphFactory(ConnectedNodeV2)
        edgesBefore = self.edgeNames(graph)

        for _ in range(2):
            snapshot = self.upgrade(graph, nodeName)
            assert isinstance(graph.node(nodeName), Node)
            assert self.edgeNames(graph) == edgesBefore

            self.undoUpgrade(graph, nodeName, snapshot)
            assert isinstance(graph.node(nodeName), CompatibilityNode)
            assert self.edgeNames(graph) == edgesBefore

    def test_undoUpgradeRestoresConnectionsLostDuringUpgrade(self, connectedGraphFactory):
        """
        'removedOutput' does not exist in the upgraded node: its connection cannot be restored by the upgrade,
        but the undo must bring it back along with the CompatibilityNode.
        """
        graph, nodeName = connectedGraphFactory(ConnectedNodeV3)
        edgesBefore = self.edgeNames(graph)
        lostEdges = {edge for edge in edgesBefore if edge[0] == f"{nodeName}.removedOutput"}
        assert len(lostEdges) == 1
        # The list the lost edge was connected to: the entry is neither kept empty by the upgrade nor duplicated by the undo
        listName = next(iter(lostEdges))[1].split("[")[0]
        assert len(graph.attribute(listName)) == 2

        snapshot = self.upgrade(graph, nodeName)
        assert self.edgeNames(graph) == edgesBefore - lostEdges
        assert len(graph.attribute(listName)) == 1

        self.undoUpgrade(graph, nodeName, snapshot)

        assert isinstance(graph.node(nodeName), CompatibilityNode)
        assert self.edgeNames(graph) == edgesBefore
        assert len(graph.attribute(listName)) == 2
