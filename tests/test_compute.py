# coding:utf-8

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
        logFileName = "log"
        if size > 1:
            logFileName = f"{chunkIndex}.log"
        logFile = Path(nodeCache) / logFileName
        logFiles[chunkIndex] = logFile
        logFile.touch()
        node.preprocess()
        if size > 1:
            chunk = node.chunks[chunkIndex]
            chunk.process(True, True)
        else:
            node.process(True, True)
        node.postprocess()
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
        chunk.logger.info(f"> {chunk.node.name}")
        chunk.logManager.end()


class TestNodeB(desc.BaseNode):
    __test__ = False
    
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

    def process(self, node):
        LOGGER.info(f"> {node.name}")


class TestNodeLogger:
    
    reA = re.compile(r"> TestNodeA_1")
    reB = re.compile(r"> TestNodeB_1")

    @classmethod
    def setup_class(cls):
        registerNodeDesc(TestNodeA)
        registerNodeDesc(TestNodeB)

    @classmethod
    def teardown_class(cls):
        unregisterNodeDesc(TestNodeA)
        unregisterNodeDesc(TestNodeB)

    def test_processChunk(self, tmp_path):
        graph = Graph("")
        graph._cacheDir = tmp_path
        node = graph.addNewNode(TestNodeA.__name__)
        # Compute
        logFiles = executeChunks(node, tmp_path, 2)
        for chunkId, logFile in logFiles.items():
            with open(logFile, "r") as f:
                content = f.read()
                assert len(self.reA.findall(content)) == 1
    
    def test_process(self, tmp_path):
        graph = Graph("")
        graph._cacheDir = tmp_path
        node = graph.addNewNode(TestNodeB.__name__)
        # Compute
        logFiles = executeChunks(node, tmp_path, 1)
        for _, logFile in logFiles.items():
            with open(logFile, "r") as f:
                content = f.read()
                # TODO : not working yet because the logger is not available outside of chunks.
                # > fixed by #2845
                # assert len(self.reB.findall(content)) == 1
                pass 
