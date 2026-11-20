#!/usr/bin/env python
# coding:utf-8

import os
from unittest.mock import patch

import pytest

from meshroom.core import desc
from meshroom.core.graph import Graph, executeGraph
from meshroom.core.node import Status

from .utils import registeredNodeTypes


# State shared by the nodes computed in the test process, standing for a scene opened in a DCC
_session = {}


class OpenSession(desc.Node):
    """ Open the session that the next nodes edit. """
    inputs = []
    outputs = [
        desc.StringParam(name="session", label="Session", description="Session.", value="{nodeCacheFolder}"),
    ]

    def processChunk(self, chunk):
        _session["pid"] = os.getpid()
        _session["edits"] = []


class EditSession(desc.Node):
    """ Edit the session opened by a previous node in the same process. """
    inputs = [
        desc.StringParam(name="session", label="Session", description="Session.", value=""),
    ]
    outputs = [
        desc.StringParam(name="output", label="Output", description="Output.", value="{nodeCacheFolder}"),
    ]

    def processChunk(self, chunk):
        if _session.get("pid") != os.getpid():
            raise RuntimeError("No session opened in this process.")
        _session["edits"].append(chunk.node.name)


class FailOnceOnLastChunk(desc.Node):
    """ Two chunks; the last one fails on the first computation. """
    size = desc.StaticNodeSize(2)
    parallelization = desc.Parallelization(blockSize=1)
    inputs = []
    outputs = [
        desc.StringParam(name="output", label="Output", description="Output.", value="{nodeCacheFolder}"),
    ]
    failed = False

    def processChunk(self, chunk):
        if chunk.range.iteration == 1 and not FailOnceOnLastChunk.failed:
            FailOnceOnLastChunk.failed = True
            raise RuntimeError("First computation of the last chunk fails.")


def _sessionGraph(graph: Graph):
    """ Add an OpenSession node followed by two EditSession nodes to 'graph'. """
    openNode = graph.addNewNode("OpenSession")
    editA = graph.addNewNode("EditSession", session=openNode.session)
    editB = graph.addNewNode("EditSession", session=editA.output)
    return openNode, editA, editB


def test_nodesShareTheProcessWhenComputedInCurrentEnv(graphSavedOnDisk):
    _session.clear()
    with registeredNodeTypes([OpenSession, EditSession]):
        graph: Graph = graphSavedOnDisk
        openNode, editA, editB = _sessionGraph(graph)

        executeGraph(graph, inCurrentEnv=True)

        assert _session["edits"] == [editA.name, editB.name]
        for node in (openNode, editA, editB):
            assert node.getGlobalStatus() == Status.SUCCESS
            # The chunk logs are written as when computed by meshroom_compute
            assert os.path.exists(node.chunks[0].getLogFile())


def test_nodesAreComputedInTheirEnvByDefault(graphSavedOnDisk):
    _session.clear()
    with registeredNodeTypes([OpenSession, EditSession]), \
            patch.object(desc.Node, "processChunkInEnvironment", autospec=True) as processChunkInEnvironment:
        graph: Graph = graphSavedOnDisk
        nodes = _sessionGraph(graph)

        executeGraph(graph)

        # Each node is run in its own process: none of them is computed in this one
        assert _session == {}
        assert [call.args[1].node.name for call in processChunkInEnvironment.call_args_list] == [node.name for node in nodes]


def test_finishedChunkLogIsKeptWhenRecomputedInCurrentEnv(graphSavedOnDisk):
    FailOnceOnLastChunk.failed = False
    with registeredNodeTypes([FailOnceOnLastChunk]):
        graph: Graph = graphSavedOnDisk
        node = graph.addNewNode("FailOnceOnLastChunk")

        with pytest.raises(RuntimeError):
            executeGraph(graph, inCurrentEnv=True)
        finishedChunk = node.chunks[0]
        assert finishedChunk.isFinished()
        with open(finishedChunk.getLogFile()) as f:
            log = f.read()
        assert log

        # Only the failed chunk is recomputed: the log of the finished one is untouched
        executeGraph(graph, inCurrentEnv=True)
        assert node.getGlobalStatus() == Status.SUCCESS
        with open(finishedChunk.getLogFile()) as f:
            assert f.read() == log
