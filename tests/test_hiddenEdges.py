"""Tests of the hidden edges of the graph editor (meshroom.core.hiddenEdges)."""
from meshroom.core import desc, hiddenEdges
from meshroom.core.graph import Graph, loadGraph

from .utils import registerNodeDesc, unregisterNodeDesc


class NodeWithInputs(desc.Node):
    inputs = [
        desc.File(name="input", label="Input", description="", value=""),
        desc.ListAttribute(name="inputs", label="Inputs", description="",
                           elementDesc=desc.File(name="file", label="File", description="", value="")),
    ]
    outputs = [desc.File(name="output", label="Output", description="", value="{nodeCacheFolder}/out")]


def setup_module():
    registerNodeDesc(NodeWithInputs)


def teardown_module():
    unregisterNodeDesc(NodeWithInputs)


def test_hiddenInputsAreSavedAndDoNotInvalidate(tmp_path):
    graph = Graph("")
    a = graph.addNewNode("NodeWithInputs")
    b = graph.addNewNode("NodeWithInputs")
    graph.addEdge(a.output, b.input)
    uid = b._uid
    attribute = b.internalAttribute(hiddenEdges.HIDDEN_INPUTS)
    attribute.value = hiddenEdges.withNames(attribute.value, ["input"], True)
    assert hiddenEdges.isHidden(b.input) and hiddenEdges.hiddenNames(b) == ["input"]
    assert b._uid == uid
    path = str(tmp_path / "graph.mg")
    graph.save(path)
    loaded = loadGraph(path)
    assert hiddenEdges.isHidden(loaded.node(b.name).input)
    # Shown again
    attribute.value = hiddenEdges.withNames(attribute.value, ["input"], False)
    assert not hiddenEdges.isHidden(b.input)


def test_relativeNames():
    graph = Graph("")
    node = graph.addNewNode("NodeWithInputs")
    node.inputs.append("")
    assert hiddenEdges.relativeName(node.input) == "input"
    assert hiddenEdges.relativeName(node.inputs.at(0)) == "inputs[0]"


def test_afterListRemoval():
    value = "input,inputs[0],inputs[2],inputs[3].x,mask,inputs2[3]"
    # Removing the element 1: the hidden 2 and 3 become 1 and 2; other inputs are kept
    assert hiddenEdges.afterListRemoval(value, "inputs", 1) == "input,inputs[0],inputs[1],inputs[2].x,mask,inputs2[3]"
    # Removing a hidden element forgets it
    assert hiddenEdges.afterListRemoval(value, "inputs", 0) == "input,inputs[1],inputs[2].x,mask,inputs2[3]"
    assert hiddenEdges.afterListRemoval(value, "inputs", 5) == value
    assert hiddenEdges.afterListRemoval("", "inputs", 0) == ""
