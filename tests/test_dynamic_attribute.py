"""Tests for the DynamicAttribute feature."""
import pytest

from meshroom.core import desc
from meshroom.core.attribute import DynamicAttribute as DynamicAttributeInstance
from meshroom.core.desc import DynamicAttribute as DynamicAttributeDesc
from meshroom.core.graph import Graph


# ---------------------------------------------------------------------------
# Descriptor tests
# ---------------------------------------------------------------------------

def test_dynamic_attribute_desc_type():
    """DynamicAttribute descriptor has the correct type string."""
    d = DynamicAttributeDesc(name="dynInputs")
    assert d.type == "DynamicAttribute"


def test_dynamic_attribute_desc_instance_type():
    """DynamicAttribute descriptor returns the correct instance class."""
    d = DynamicAttributeDesc(name="dynInputs")
    assert d.instanceType is DynamicAttributeInstance


# ---------------------------------------------------------------------------
# Node / attribute creation tests
# ---------------------------------------------------------------------------

def test_dynamic_attribute_present_on_node():
    """A node that declares a DynamicAttribute exposes it as an attribute."""
    graph = Graph("test")
    node = graph.addNewNode("DynamicInputsNode")
    assert node.hasAttribute("dynInputs")
    dynAttr = node.attribute("dynInputs")
    assert isinstance(dynAttr, DynamicAttributeInstance)


def test_dynamic_attribute_validates_any_connection():
    """DynamicAttribute.validateIncomingConnection returns True for any type."""
    graph = Graph("test")
    node = graph.addNewNode("DynamicInputsNode")
    dynAttr = node.attribute("dynInputs")

    # Build a fake source attribute of type File
    srcNode = graph.addNewNode("Ls", input="/tmp")
    assert dynAttr.validateIncomingConnection(srcNode.output)


# ---------------------------------------------------------------------------
# Dynamic input creation tests (via Node.addDynamicInput / removeDynamicInput)
# ---------------------------------------------------------------------------

def test_add_dynamic_input_creates_sibling_attribute():
    """Adding a dynamic input inserts a new attribute before the DynamicAttribute."""
    graph = Graph("test")
    srcNode = graph.addNewNode("Ls", input="/tmp")
    dstNode = graph.addNewNode("DynamicInputsNode")

    dynAttr = dstNode.attribute("dynInputs")
    srcDesc = srcNode.attribute("output")._desc

    newAttr = dstNode.addDynamicInput("dynInputs_0", srcDesc, dynAttr)
    assert newAttr is not None
    assert dstNode.hasAttribute("dynInputs_0")
    assert getattr(newAttr, "_isDynamic", False) is True
    assert "dynInputs_0" in dstNode._dynamicInputs
    assert dstNode._dynamicInputs["dynInputs_0"] == "dynInputs"

    # The new attribute should appear BEFORE dynAttr in the attributes list
    attrList = list(dstNode._attributes)
    dynIdx = attrList.index(dynAttr)
    newIdx = attrList.index(newAttr)
    assert newIdx < dynIdx


def test_remove_dynamic_input():
    """Removing a dynamic input deletes the attribute from the node."""
    graph = Graph("test")
    srcNode = graph.addNewNode("Ls", input="/tmp")
    dstNode = graph.addNewNode("DynamicInputsNode")

    dynAttr = dstNode.attribute("dynInputs")
    srcDesc = srcNode.attribute("output")._desc

    dstNode.addDynamicInput("dynInputs_0", srcDesc, dynAttr)
    assert dstNode.hasAttribute("dynInputs_0")

    dstNode.removeDynamicInput("dynInputs_0")
    assert not dstNode.hasAttribute("dynInputs_0")
    assert "dynInputs_0" not in dstNode._dynamicInputs


# ---------------------------------------------------------------------------
# Serialization / deserialization tests
# ---------------------------------------------------------------------------

def test_dynamic_inputs_serialized_in_todict():
    """Dynamic inputs are included in the node's serialized form."""
    graph = Graph("test")
    srcNode = graph.addNewNode("Ls", input="/tmp")
    dstNode = graph.addNewNode("DynamicInputsNode")

    dynAttr = dstNode.attribute("dynInputs")
    srcDesc = srcNode.attribute("output")._desc

    newAttr = dstNode.addDynamicInput("dynInputs_0", srcDesc, dynAttr)

    nodeDict = dstNode.toDict()
    assert "dynamicInputs" in nodeDict
    assert "dynInputs_0" in nodeDict["dynamicInputs"]
    typeName, ownerName = nodeDict["dynamicInputs"]["dynInputs_0"]
    assert typeName == "File"
    assert ownerName == "dynInputs"


def test_dynamic_inputs_restored_after_load(tmp_path):
    """Dynamic inputs survive a graph save/load cycle."""
    import os
    from meshroom.core.graph import loadGraph

    graph = Graph("test")
    srcNode = graph.addNewNode("Ls", input="/tmp")
    dstNode = graph.addNewNode("DynamicInputsNode")

    dynAttr = dstNode.attribute("dynInputs")
    srcDesc = srcNode.attribute("output")._desc

    newAttr = dstNode.addDynamicInput("dynInputs_0", srcDesc, dynAttr)
    # Connect source to new dynamic input
    srcNode.output.connectTo(newAttr)

    graphFile = str(tmp_path / "graph.mg")
    graph.save(graphFile)

    # Reload
    loadedGraph = loadGraph(graphFile)
    loadedDstNode = loadedGraph.node(dstNode.name)

    assert loadedDstNode.hasAttribute("dynInputs_0"), \
        "Dynamic input should be present after load"
    loadedAttr = loadedDstNode.attribute("dynInputs_0")
    assert getattr(loadedAttr, "_isDynamic", False) is True
    assert loadedAttr.isLink, "Dynamic input should still be connected after load"
