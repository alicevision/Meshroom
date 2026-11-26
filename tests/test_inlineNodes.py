# coding:utf-8

import json
import os
from collections import Counter
from pathlib import Path

import pytest

from meshroom.core import desc
from meshroom.core.graph import executeGraph, loadGraph
from meshroom.core.node import Status

from .utils import registeredNodeTypes


_INPUTS = [desc.StringParam(name="input", label="Input", description="", value="")]
_OUTPUTS = [desc.StringParam(name="output", label="Output", description="", value=None)]


class InlineAppend(desc.InlineNode):
    inputs = _INPUTS
    outputs = _OUTPUTS

    def process(self, node):
        node.output.value = node.input.value + "i"


class InlineFail(InlineAppend):
    def process(self, node):
        raise RuntimeError("Inline failure")


class RegularAppend(desc.BaseNode):
    inputs = _INPUTS
    outputs = _OUTPUTS

    def process(self, node):
        node.output.value = node.input.value + "r"


class ParallelAppend(desc.BaseNode):
    size = desc.DynamicNodeSize("input")
    parallelization = desc.Parallelization(blockSize=1)
    inputs = _INPUTS
    outputs = _OUTPUTS

    def processChunk(self, chunk):
        chunk.node.output.value = chunk.node.input.value + "p"


class SizedInlineAppend(InlineAppend):
    size = desc.DynamicNodeSize("input")


class ParallelCount(desc.BaseNode):
    size = desc.DynamicNodeSize("count")
    parallelization = desc.Parallelization(blockSize=1)
    inputs = [desc.IntParam(name="count", label="Count", description="", value=3, range=None)]
    outputs = _OUTPUTS

    def processChunk(self, chunk):
        chunk.node.output.value = "c"


class CountedInline(InlineAppend):
    calls = Counter()  # Number of evaluations per node name

    def process(self, node):
        CountedInline.calls[node.name] += 1
        super().process(node)


class SizedCountedInline(CountedInline):
    size = desc.DynamicNodeSize("input")


class InlineJoin(desc.InlineNode):
    inputs = [
        desc.StringParam(name="first", label="First", description="", value=""),
        desc.StringParam(name="second", label="Second", description="", value=""),
    ]
    outputs = _OUTPUTS

    def process(self, node):
        node.output.value = node.first.value + node.second.value


@pytest.fixture(autouse=True)
def nodeTypes():
    nodeTypes = [InlineAppend, InlineFail, SizedInlineAppend, CountedInline, SizedCountedInline, InlineJoin,
                 RegularAppend, ParallelAppend, ParallelCount]
    CountedInline.calls.clear()
    with registeredNodeTypes(nodeTypes):
        yield


def createChain(graph):
    """ Create and save the chain: upstream (regular) -> inlineA -> inlineB -> downstream (regular). """
    upstream = graph.addNewNode("RegularAppend")
    inlineA = graph.addNewNode("InlineAppend")
    inlineB = graph.addNewNode("InlineAppend")
    downstream = graph.addNewNode("RegularAppend")
    upstream.output.connectTo(inlineA.input)
    inlineA.output.connectTo(inlineB.input)
    inlineB.output.connectTo(downstream.input)
    graph.save()
    return upstream, inlineA, inlineB, downstream


def test_inlineNodesAreEvaluatedByDownstreamNodes(graphSavedOnDisk):
    upstream, inlineA, inlineB, downstream = createChain(graphSavedOnDisk)

    assert not inlineA.isComputableType
    assert not inlineA.chunks

    executeGraph(graphSavedOnDisk)

    assert downstream.output.value == "riir"
    assert not os.path.exists(inlineA.internalFolder)
    assert not os.path.exists(inlineB.internalFolder)


def test_inlineNodesAreEvaluatedWhenLoadedFromDisk(graphSavedOnDisk):
    """ A node computed in its own process only gets the upstream values persisted in the cache. """
    upstream, _, _, downstream = createChain(graphSavedOnDisk)
    executeGraph(graphSavedOnDisk, toNodes=[upstream])

    graph = loadGraph(graphSavedOnDisk.filepath)
    graph.update()
    node = graph.node(downstream.name)
    assert node.input.value is None

    node.process(forceCompute=True, inCurrentEnv=True)

    assert node.output.value == "riir"


def test_inlineNodesAreNotScheduled(graphSavedOnDisk):
    """ Downstream nodes must wait for the nodes read by a shared inline node. """
    graph = graphSavedOnDisk
    upstream, inlineA, inlineB, downstream = createChain(graph)
    otherDownstream = graph.addNewNode("RegularAppend")
    inlineB.output.connectTo(otherDownstream.input)

    nodes, edges = graph.dfsToProcess()

    assert set(nodes) == {upstream, downstream, otherDownstream}
    expectedEdges = {(downstream, upstream), (otherDownstream, upstream)}
    assert set(edges) == expectedEdges
    assert set(graph.flowEdges()) == expectedEdges


def test_bypassedEdgesAreUnique(graphSavedOnDisk):
    """ A node reading the same upstream node through several inline nodes depends on it once. """
    graph = graphSavedOnDisk
    upstream = graph.addNewNode("RegularAppend")
    inlineA = graph.addNewNode("InlineAppend")
    inlineB = graph.addNewNode("InlineAppend")
    join = graph.addNewNode("InlineJoin")
    downstream = graph.addNewNode("RegularAppend")
    upstream.output.connectTo(inlineA.input)
    upstream.output.connectTo(inlineB.input)
    inlineA.output.connectTo(join.first)
    inlineB.output.connectTo(join.second)
    join.output.connectTo(downstream.input)
    graph.save()

    _, edges = graph.dfsToProcess()

    assert edges == [(downstream, upstream)]
    assert graph.flowEdges() == [(downstream, upstream)]


def test_inlineNodeFailureIsReportedOnDownstreamNode(graphSavedOnDisk):
    graph = graphSavedOnDisk
    inline = graph.addNewNode("InlineFail")
    downstream = graph.addNewNode("RegularAppend")
    inline.output.connectTo(downstream.input)
    graph.save()

    with pytest.raises(RuntimeError, match="Inline failure"):
        executeGraph(graph)

    assert downstream.getGlobalStatus() == Status.ERROR


def test_staleStatusFileIsIgnored(graphSavedOnDisk):
    """ The cache of a node type that used to be computed must not bring chunks back. """
    inline = graphSavedOnDisk.addNewNode("InlineAppend")
    statusFile = Path(inline.nodeStatusFile)
    statusFile.parent.mkdir(parents=True)
    statusFile.write_text(json.dumps({"status": "SUCCESS", "chunksBlockSize": 1, "chunksFullSize": 1, "chunksNbBlocks": 1}))

    inline.updateStatusFromCache()

    assert not inline.chunks
    assert inline.getGlobalStatus() == Status.NONE


def test_parallelNodeSizedByInlineNode(graphSavedOnDisk):
    graph = graphSavedOnDisk
    inline = graph.addNewNode("InlineAppend")
    downstream = graph.addNewNode("ParallelAppend")
    inline.output.connectTo(downstream.input)
    graph.save()

    executeGraph(graph)

    assert len(downstream.chunks) == 1
    assert downstream.output.value == "ip"


def test_inlineNodeSizeIsUpdatedBeforeDownstreamChunks(graphSavedOnDisk):
    """ The size of an inline node must follow its upstream node, only sized during the compute. """
    graph = graphSavedOnDisk
    upstream = graph.addNewNode("ParallelCount")
    inline = graph.addNewNode("SizedInlineAppend")
    downstream = graph.addNewNode("ParallelAppend")
    upstream.output.connectTo(inline.input)
    inline.output.connectTo(downstream.input)
    graph.save()

    executeGraph(graph)

    assert len(upstream.chunks) == 3
    assert len(downstream.chunks) == 3


def test_inlineOutputIsResetWhenInvalidated(graphSavedOnDisk):
    graph = graphSavedOnDisk
    upstream, _, inlineB, _ = createChain(graph)
    executeGraph(graph)
    assert inlineB.output.value == "rii"

    upstream.input.value = "changed"
    graph.update()

    assert inlineB.output.value is None


def test_inlineNodeFailureWhenCreatingChunks(graphSavedOnDisk):
    graph = graphSavedOnDisk
    inline = graph.addNewNode("InlineFail")
    downstream = graph.addNewNode("ParallelAppend")
    inline.output.connectTo(downstream.input)
    graph.save()

    with pytest.raises(RuntimeError, match="Inline failure"):
        executeGraph(graph)

    assert downstream.getGlobalStatus() == Status.ERROR


def test_inlineNodeIsEvaluatedOnceForAllChunks(graphSavedOnDisk):
    """ createChunks and each chunk of the downstream node must not evaluate the inline node again. """
    graph = graphSavedOnDisk
    upstream = graph.addNewNode("ParallelCount")
    inline = graph.addNewNode("SizedCountedInline")
    downstream = graph.addNewNode("ParallelAppend")
    upstream.output.connectTo(inline.input)
    inline.output.connectTo(downstream.input)
    graph.save()

    executeGraph(graph)

    assert len(downstream.chunks) == 3
    assert downstream.output.value == "cip"
    assert CountedInline.calls[inline.name] == 1


def test_sharedInlineNodeIsEvaluatedOnce(graphSavedOnDisk):
    """ An inline node read through several inline paths is evaluated once. """
    graph = graphSavedOnDisk
    shared = graph.addNewNode("CountedInline")
    left = graph.addNewNode("CountedInline")
    right = graph.addNewNode("CountedInline")
    join = graph.addNewNode("InlineJoin")
    downstream = graph.addNewNode("RegularAppend")
    shared.output.connectTo(left.input)
    shared.output.connectTo(right.input)
    left.output.connectTo(join.first)
    right.output.connectTo(join.second)
    join.output.connectTo(downstream.input)
    graph.save()

    executeGraph(graph)

    assert downstream.output.value == "iiiir"
    assert CountedInline.calls == {shared.name: 1, left.name: 1, right.name: 1}


def test_inlineNodeIsEvaluatedAgainWhenInvalidated(graphSavedOnDisk):
    graph = graphSavedOnDisk
    upstream = graph.addNewNode("RegularAppend")
    inline = graph.addNewNode("CountedInline")
    downstream = graph.addNewNode("RegularAppend")
    upstream.output.connectTo(inline.input)
    inline.output.connectTo(downstream.input)
    graph.save()
    executeGraph(graph)
    assert downstream.output.value == "rir"

    upstream.input.value = "changed"
    graph.update()
    executeGraph(graph)

    assert downstream.output.value == "changedrir"
    assert CountedInline.calls[inline.name] == 2


def test_leafInlineNodeIsEvaluatedOnceItsInputsAreComputed(graphSavedOnDisk):
    """ The graph evaluates inline nodes outside of a compute, even with no downstream node. """
    graph = graphSavedOnDisk
    upstream = graph.addNewNode("RegularAppend")
    inline = graph.addNewNode("CountedInline")
    upstream.output.connectTo(inline.input)
    graph.save()

    graph.evaluateInlineNodes()
    assert inline.output.value is None
    assert CountedInline.calls[inline.name] == 0

    executeGraph(graph)
    graph.evaluateInlineNodes()
    graph.evaluateInlineNodes()

    assert inline.output.value == "ri"
    assert CountedInline.calls[inline.name] == 1


def test_inlineNodeWithoutComputableInputIsEvaluated(graphSavedOnDisk):
    graph = graphSavedOnDisk
    inlineA = graph.addNewNode("InlineAppend")
    inlineB = graph.addNewNode("InlineAppend")
    inlineA.output.connectTo(inlineB.input)

    graph.evaluateInlineNodes()

    assert inlineB.output.value == "ii"


def test_inlineNodeFailureIsReportedOnComputeAfterEvaluation(graphSavedOnDisk):
    """ A failure when the graph evaluates inline nodes is ignored, and still reported by the downstream compute. """
    graph = graphSavedOnDisk
    inline = graph.addNewNode("InlineFail")
    downstream = graph.addNewNode("RegularAppend")
    inline.output.connectTo(downstream.input)
    graph.save()

    graph.evaluateInlineNodes()

    with pytest.raises(RuntimeError, match="Inline failure"):
        executeGraph(graph)
    assert downstream.getGlobalStatus() == Status.ERROR
