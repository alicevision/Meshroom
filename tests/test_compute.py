# coding:utf-8

"""
In this test we test the code that is usually launched directly from the meshroom_compute script

TODO : We could directly test by launching the executable (`desc.node._MESHROOM_COMPUTE_EXE`)
"""

import os
import re
from pathlib import Path
import logging

from meshroom.core.graph import Graph
from meshroom.core import desc
from .utils import registerNodeDesc, unregisterNodeDesc

LOGGER = logging.getLogger("TestCompute")


def executeChunks(node, size):
    os.makedirs(node.internalFolder)
    logFiles = {}
    for chunkIndex in range(size):
        iteration = chunkIndex if size > 1 else -1
        logFileName = "log"
        if size > 1:
            logFileName = f"{chunkIndex}.log"
        logFile = Path(node.internalFolder) / logFileName
        logFiles[chunkIndex] = logFile
        logFile.touch()
        node.prepareLogger(iteration)
        node.preprocess()
        if size > 1:
            chunk = node.chunks[chunkIndex]
            chunk.process(True, True)
        else:
            node.process(True, True)
        node.postprocess()
        node.restoreLogger()
    return logFiles


_INPUTS = [
    desc.IntParam(
        name="input",
        label="Input",
        description="input",
        value=0,
    ),
]
_OUTPUTS = [
    desc.IntParam(
        name="output",
        label="Output",
        description="Output",
        value=None,
    ),
]

class TestNodeA(desc.BaseNode):
    """
    Test process with chunks
    """
    __test__ = False
    _size = 2
    size = desc.StaticNodeSize(2)
    parallelization = desc.Parallelization(blockSize=1)
    inputs = _INPUTS
    outputs = _OUTPUTS

    def processChunk(self, chunk):
        chunk.logManager.start("info")
        iteration = chunk.range.iteration
        nbBlocks = chunk.range.nbBlocks
        chunk.logger.info(f"> (chunk.logger) {chunk.node.name}")
        LOGGER.info(f"> (root logger) {iteration}/{nbBlocks}")
        chunk.logManager.end()


class TestNodeB(TestNodeA):
    """
    Test process with 1 chunk but still implementing processChunk
    """
    __test__ = False
    _size = 1
    size = desc.StaticNodeSize(1)
    parallelization = None


class TestNodeC(desc.BaseNode):
    """
    Test process without chunks and without processChunk
    """
    __test__ = False
    size = desc.StaticNodeSize(1)
    parallelization = None
    inputs = _INPUTS
    outputs = _OUTPUTS

    def process(self, node):
        LOGGER.info(f"> {node.name}")


class TestNodeLogger:

    logPrefix = r"\[\d{2}:\d{2}:\d{2}\.\d{3}\]\[info\] > "

    @classmethod
    def setup_class(cls):
        registerNodeDesc(TestNodeA)
        registerNodeDesc(TestNodeB)
        registerNodeDesc(TestNodeC)

    @classmethod
    def teardown_class(cls):
        unregisterNodeDesc(TestNodeA)
        unregisterNodeDesc(TestNodeB)
        unregisterNodeDesc(TestNodeC)

    def test_processChunks(self, tmp_path):
        graph = Graph("")
        graph._cacheDir = tmp_path
        # TestNodeA : multiple chunks
        node = graph.addNewNode(TestNodeA.__name__)
        # Compute
        logFiles = executeChunks(node, 2)
        for chunkIndex, logFile in logFiles.items():
            with open(logFile, "r") as f:
                content = f.read()
                reg = re.compile(self.logPrefix + r"\(chunk.logger\) TestNodeA_1")
                assert len(reg.findall(content)) == 1
                reg = re.compile(self.logPrefix + r"\(root logger\) " + f"{chunkIndex}/2")
                assert len(reg.findall(content)) == 1
        # TestNodeA : single chunk
        nodeB = graph.addNewNode(TestNodeB.__name__)
        logFiles = executeChunks(nodeB, 1)
        for chunkIndex, logFile in logFiles.items():
            with open(logFile, "r") as f:
                content = f.read()
                reg = re.compile(self.logPrefix + r"\(chunk.logger\) TestNodeB_1")
                assert len(reg.findall(content)) == 1
                reg = re.compile(self.logPrefix + r"\(root logger\) 0/0")
                assert len(reg.findall(content)) == 1

    def test_process(self, tmp_path):
        graph = Graph("")
        graph._cacheDir = tmp_path
        node = graph.addNewNode(TestNodeC.__name__)
        # Compute
        logFiles = executeChunks(node, 1)
        for _, logFile in logFiles.items():
            with open(logFile, "r") as f:
                content = f.read()
                reg = re.compile(self.logPrefix + "TestNodeC_1")
                assert len(reg.findall(content)) == 1
