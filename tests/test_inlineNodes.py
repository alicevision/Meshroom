# coding:utf-8

import json
import os
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


@pytest.fixture(autouse=True)
def nodeTypes():
    with registeredNodeTypes([InlineAppend, InlineFail, RegularAppend, ParallelAppend]):
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
