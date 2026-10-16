"""Tests of the tree layout of the graph editor (meshroom.core.graphLayout)."""
from meshroom.core import desc, graphLayout
from meshroom.core.graph import Graph
from meshroom.core.node import Position

from .utils import registerNodeDesc, unregisterNodeDesc


class LayoutSource(desc.Node):
    inputs = []
    outputs = [desc.File(name="output", label="Output", description="", value="{nodeCacheFolder}/out")]


class LayoutFilter(desc.Node):
    inputs = [
        desc.File(name="input", label="Input", description="", value=""),
        desc.File(name="mask", label="Mask", description="", value=""),
        desc.IntParam(name="size", label="Size", description="", value=1, range=None),
    ]
    outputs = [desc.File(name="output", label="Output", description="", value="{nodeCacheFolder}/out")]


class LayoutMerge(desc.Node):
    inputs = [
        desc.File(name="B", label="B", description="", value=""),
        desc.File(name="A", label="A", description="", value=""),
    ]
    outputs = [desc.File(name="output", label="Output", description="", value="{nodeCacheFolder}/out")]


def setup_module():
    for nodeDesc in (LayoutSource, LayoutFilter, LayoutMerge):
        registerNodeDesc(nodeDesc)


def teardown_module():
    for nodeDesc in (LayoutSource, LayoutFilter, LayoutMerge):
        unregisterNodeDesc(nodeDesc)


def _layout(graph, nodes):
    edges = graphLayout.layoutEdges(graph, nodes)
    return graphLayout.treeLayout(nodes, edges, lambda node: (100.0, 50.0), (0.0, 0.0),
                                  lambda node: (node.x, node.y), columnSpacing=20.0, rowSpacing=10.0)


def test_inputsStackedInTheirOrder():
    graph = Graph("layout")
    plate = graph.addNewNode("LayoutSource")
    mask = graph.addNewNode("LayoutSource")
    filterNode = graph.addNewNode("LayoutFilter")
    background = graph.addNewNode("LayoutSource")
    merge = graph.addNewNode("LayoutMerge")
    graph.addEdge(plate.output, filterNode.input)
    graph.addEdge(mask.output, filterNode.mask)
    graph.addEdge(background.output, merge.B)
    graph.addEdge(filterNode.output, merge.A)
    positions = _layout(graph, [plate, filterNode, mask, background, merge])
    # Left to right: each input just left of the node using it
    assert positions[merge][0] == 240.0
    assert positions[filterNode][0] == positions[background][0] == 120.0
    assert positions[plate][0] == positions[mask][0] == 0.0
    # B on the row of the merge, A below; the inputs of the filter: input on its row, mask below
    assert positions[background][1] == positions[merge][1] == 0.0
    assert positions[filterNode][1] == 60.0
    assert positions[plate][1] == 60.0 and positions[mask][1] == 120.0


def test_sharedInputAndSeparateTrees():
    graph = Graph("layout")
    source = graph.addNewNode("LayoutSource")
    first = graph.addNewNode("LayoutFilter")
    second = graph.addNewNode("LayoutFilter")
    other = graph.addNewNode("LayoutSource")
    graph.addEdge(source.output, first.input)
    graph.addEdge(source.output, second.input)
    # A link between parameters does not count
    graph.addEdge(first.attribute("size"), second.attribute("size"))
    second.position = Position(0, 500)
    other.position = Position(0, 900)
    nodes = [source, first, second, other]
    assert len(graphLayout.layoutEdges(graph, nodes)) == 2
    positions = _layout(graph, nodes)
    # The shared input is placed once, with the highest of its outputs; the trees keep their vertical order
    assert positions[source] == (0.0, 0.0) and positions[first] == (120.0, 0.0)
    assert positions[second][1] > positions[first][1]
    assert positions[other][1] > positions[second][1]
