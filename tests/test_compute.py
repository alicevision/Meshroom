# coding:utf-8

"""
In this test we test the code that is usually launched directly from the meshroom_compute script

TODO : Directly test by launching the executable
- We can get the path with `desc.node._MESHROOM_COMPUTE_EXE`
- However this is not implemented yet because it requires to create a plugin that meshroom could discover
  and I didn't want to create a plugin just for what I'm doing here right now (which is testing the logger)
"""

import os
import re
from pathlib import Path
import logging

from meshroom.core.graph import Graph
from meshroom.core import desc
from .utils import registerNodeDesc, unregisterNodeDesc

LOGGER = logging.getLogger("TestCompute")


def executeChunks(node, tmpPath, size):
    nodeCache = os.path.join(tmpPath, node.internalFolder)
    os.makedirs(nodeCache)
    logFiles = {}
    for chunkIndex in range(size):
        iteration = chunkIndex if size > 1 else -1
        logFileName = "log"
        if size > 1:
            logFileName = f"{chunkIndex}.log"
        logFile = Path(nodeCache) / logFileName
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


class TestNodeA(desc.BaseNode):
    __test__ = False
    
    size = desc.StaticNodeSize(2)
    parallelization = desc.Parallelization(blockSize=1)

    inputs = [
        desc.IntParam(
            name="input",
            label="Input",
            description="input",
            value=0,
        ),
    ]
    outputs = [
        desc.IntParam(
            name="output",
            label="Output",
            description="Output",
            value=None,
        ),
    ]

    def processChunk(self, chunk):
        chunk.logManager.start("info")
        chunk.logger.info("> Message A")
        LOGGER.info(f"> Message B")
        chunk.logManager.end()


class TestNodeB(TestNodeA):
    size = desc.StaticNodeSize(1)
    parallelization = None


class TestNodeLogger:
    
    reA = re.compile(r"\[\d{2}:\d{2}:\d{2}\.\d{3}\]\[info\] > Message A")
    reB = re.compile(r"\[\d{2}:\d{2}:\d{2}\.\d{3}\]\[info\] > Message B")

    @classmethod
    def setup_class(cls):
        registerNodeDesc(TestNodeA)
        registerNodeDesc(TestNodeB)

    @classmethod
    def teardown_class(cls):
        unregisterNodeDesc(TestNodeA)
        unregisterNodeDesc(TestNodeB)

    def test_nodeWithChunks(self, tmp_path):
        graph = Graph("")
        graph._cacheDir = tmp_path
        node = graph.addNewNode(TestNodeA.__name__)
        # Compute
        logFiles = executeChunks(node, tmp_path, 2)
        for chunkId, logFile in logFiles.items():
            with open(logFile, "r") as f:
                content = f.read()
                assert len(self.reA.findall(content)) == 1
                assert len(self.reB.findall(content)) == 1
    
    def test_nodeWithoutChunks(self, tmp_path):
        graph = Graph("")
        graph._cacheDir = tmp_path
        node = graph.addNewNode(TestNodeB.__name__)
        # Compute
        logFiles = executeChunks(node, tmp_path, 1)
        for _, logFile in logFiles.items():
            with open(logFile, "r") as f:
                content = f.read()
                assert len(self.reA.findall(content)) == 1
                assert len(self.reB.findall(content)) == 1
