# coding:utf-8

"""
In this test we test the code that is usually launched directly from the meshroom_compute script

TODO : We could directly test by launching the executable (`desc.node._MESHROOM_COMPUTE_EXE`)
"""

import os
import re
import shlex
from types import SimpleNamespace
from pathlib import Path
import logging

from meshroom.core.graph import Graph, loadGraph
from meshroom.core import desc, pluginManager, loadClassesNodes
from meshroom.core.node import Status, ChunkIndex
from meshroom.core.plugins import Plugin
from .utils import registerNodeDesc, unregisterNodeDesc

LOGGER = logging.getLogger("TestCompute")


def executeChunks(node, size):
    os.makedirs(node.internalFolder)
    logFiles = {}
    node.preprocess()
    for chunkIndex in range(size):
        iteration = chunkIndex if size > 0 else ChunkIndex.NONE
        logFileName = f"{chunkIndex}.log"
        logFile = Path(node.internalFolder) / logFileName
        logFiles[chunkIndex] = logFile
        logFile.touch()
        node.prepareLogger(iteration)
        if size > 1:
            chunk = node.chunks[chunkIndex]
            chunk.process(True, True)
        else:
            node.process(True, True)
        node.restoreLogger()
    node.postprocess()
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


class TestNodeD(TestNodeC):
    """
    Implement preprocess / postprocess methods
    """
    def preprocess(self, node):
        LOGGER.info(f"> {node.name} (preprocess)")

    def postprocess(self, node):
        LOGGER.info(f"> {node.name} (postprocess)")


class TestNodeE(TestNodeC):
    """
    Implement preprocess / postprocess methods
    """
    def preprocess(self, node):
        raise RuntimeError()


class TestNodeLogger:
    """
    Test that the logger is correctly set up during the different stages of the compute and that logs are correctly
    written in the log file.
    """

    logPrefix = r"\[\d{2}:\d{2}:\d{2}\.\d{3}\]\[info\] > "

    @classmethod
    def setup_class(cls):
        registerNodeDesc(TestNodeA)
        registerNodeDesc(TestNodeB)
        registerNodeDesc(TestNodeC)
        registerNodeDesc(TestNodeD)

    @classmethod
    def teardown_class(cls):
        unregisterNodeDesc(TestNodeA)
        unregisterNodeDesc(TestNodeB)
        unregisterNodeDesc(TestNodeC)
        unregisterNodeDesc(TestNodeD)

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

    def test_processChunkInEnvironment_quotesGraphFilepathWithSpaces(self, tmp_path):
        graphFilepath = Path(tmp_path, "project with spaces", "scene with spaces.mg")
        graphFilepath.parent.mkdir()

        nodeDesc = desc.Node()
        executed = {}

        def executeChunkCommandLine(chunk, cmd, env=None):
            executed["cmd"] = cmd
            executed["env"] = env

        nodeDesc.executeChunkCommandLine = executeChunkCommandLine
        plugin = SimpleNamespace(runtimeEnv=None, commandPrefix="", commandSuffix="")
        node = SimpleNamespace(
            name="TestNode_1",
            graph=SimpleNamespace(filepath=graphFilepath.as_posix()),
            nodeDesc=SimpleNamespace(pythonExecutable="python", plugin=plugin),
            getChunks=lambda: [object(), object()],
        )
        chunk = SimpleNamespace(
            isPreprocess=False, isPostprocess=False,
            node=node, range=SimpleNamespace(iteration=1)
        )

        nodeDesc.processChunkInEnvironment(chunk)

        assert f'"{graphFilepath.as_posix()}"' in executed["cmd"]
        assert shlex.split(executed["cmd"])[2] == graphFilepath.as_posix()
        assert "--iteration 1" in executed["cmd"]

    def test_prepostprocess(self, tmp_path):
        graph = Graph("")
        graph._cacheDir = tmp_path
        node = graph.addNewNode(TestNodeD.__name__)
        # Compute
        logFiles = executeChunks(node, 1)
        chunkLog = logFiles[0]
        root = chunkLog.parent
        preprocessLog = root / "preprocess.log"
        postprocessLog = root / "postprocess.log"
        def check_file(path, suffix=""):
            with open(path, "r") as f:
                content = f.read()
                reg = re.compile(self.logPrefix + "TestNodeD_1" + suffix)
                assert len(reg.findall(content)) == 1
        check_file(preprocessLog, r" \(preprocess\)")
        check_file(chunkLog, "")
        check_file(postprocessLog, r" \(postprocess\)")


class TestLockUpdates:
    """
    Tests for node locking behaviour during status transitions. Nodes should be properly locked when they undergo
    computation statuses and unlocked when their status is reset (through parameter changes, for example).
    """
    plugin = None

    @classmethod
    def setup_class(cls):
        folder = os.path.join(os.path.dirname(__file__), "plugins", "meshroom")
        package = "pluginA"
        cls.plugin = Plugin(package, folder)
        nodes = loadClassesNodes(folder, package)
        for node in nodes:
            cls.plugin.addNodePlugin(node)
        pluginManager.addPlugin(cls.plugin)

    @classmethod
    def teardown_class(cls):
        for node in cls.plugin.nodes.values():
            pluginManager.unregisterNode(node)
        pluginManager.removePlugin(cls.plugin)
        cls.plugin = None

    @staticmethod
    def checkNodeStatusAndLock(node, expectedStatus, expectedLock):
        assert node.globalStatus == expectedStatus.name
        assert node.locked == expectedLock

    def test_lockDuringComputation(self, graphSavedOnDisk):
        """
        Test that a node is properly locked during the execution of its "process()" method and unlocked once the process
        is finished. Both the global status and the lock status should be updated throughout the process.
        """
        import threading
        import time

        graph: Graph = graphSavedOnDisk
        node = graph.addNewNode("PluginANodeA")
        graph.save()

        self.checkNodeStatusAndLock(node, Status.NONE, False)

        # PluginANodeA will sleep 3 seconds in its "process", so we can check the status and lock during the process execution
        thread = threading.Thread(target=node.process, kwargs={"inCurrentEnv": True})
        thread.start()

        time.sleep(0.5)  # Wait for the process to start and update the status
        self.checkNodeStatusAndLock(node, Status.RUNNING, True)

        # Wait for the process to finish and update the status
        thread.join()

        self.checkNodeStatusAndLock(node, Status.SUCCESS, False)

    def test_lockResetOnParameterChange(self, graphSavedOnDisk):
        """
        Test that a node's lock is properly reset when its status is reset,
        for example through parameter changes.
        """
        graph: Graph = graphSavedOnDisk
        node = graph.addNewNode("PluginANodeA")
        graph.save()

        self.checkNodeStatusAndLock(node, Status.NONE, False)
        node.process(inCurrentEnv=True)
        self.checkNodeStatusAndLock(node, Status.SUCCESS, False)

        # Change a parameter to reset the status and check that the lock is also reset
        node.input.value = "path"
        self.checkNodeStatusAndLock(node, Status.NONE, False)

    def test_lockResetOnDuplicatedParameterChange(self, graphSavedOnDisk):
        """
        Test that when a node is duplicated while running, the duplicate node is independent from the original one
        and that changing a parameter on the duplicate node resets its status and lock without impacting the original
        node's status and lock.
        """
        import threading
        import time

        graph: Graph = graphSavedOnDisk
        node = graph.addNewNode("PluginANodeA")
        graph.save()

        self.checkNodeStatusAndLock(node, Status.NONE, False)

        thread = threading.Thread(target=node.process, kwargs={"inCurrentEnv": True})
        thread.start()

        time.sleep(0.5)
        self.checkNodeStatusAndLock(node, Status.RUNNING, True)

        # Duplicate the running & locked node
        duplicate = graph.duplicateNodes([node])

        # "duplicate" is an ordered_dict with the original node as key and a list of duplicates as value.
        # We know there is only one duplicate in this test.
        assert len(duplicate) == 1
        duplicate = list(duplicate.values())[0][0]

        # Check the duplicate node is valid
        assert duplicate is not None
        assert duplicate.nodeType == node.nodeType
        assert duplicate.name != node.name

        # Check the status of the duplicate node is RUNNING but that it is not locked:
        # it has not been computed and should be independent from the original node
        self.checkNodeStatusAndLock(duplicate, Status.RUNNING, False)

        # Change a parameter to reset the duplicatenode's status and check that the lock is also reset
        duplicate.input.value = "path"
        self.checkNodeStatusAndLock(duplicate, Status.NONE, False)
        self.checkNodeStatusAndLock(node, Status.RUNNING, True)

        thread.join()

        self.checkNodeStatusAndLock(node, Status.SUCCESS, False)
        self.checkNodeStatusAndLock(duplicate, Status.NONE, False)

    def test_noLockResetOnGraphLoad(self, graphSavedOnDisk):
        """
        Test that when a graph is loaded while a node is running, the node's status and lock are not reset and that
        the node is still locked. """
        import threading
        import time

        graph: Graph = graphSavedOnDisk
        node = graph.addNewNode("PluginANodeA")
        graph.save()
        self.checkNodeStatusAndLock(node, Status.NONE, False)

        thread = threading.Thread(target=node.process, kwargs={"inCurrentEnv": True})
        thread.start()
        time.sleep(0.5)
        self.checkNodeStatusAndLock(node, Status.RUNNING, True)

        # Load the graph while the node is running and check that the node's status and lock are not reset
        loadedGraph = loadGraph(graph.filepath)
        loadedNode = loadedGraph.node(node.name)
        self.checkNodeStatusAndLock(loadedNode, Status.RUNNING, True)

        thread.join()
        # Make sure the status is up-to-date
        loadedNode.updateStatusFromCache()
        self.checkNodeStatusAndLock(loadedNode, Status.SUCCESS, False)

    def test_noDownstreamNodeLockDuringComputation(self, graphSavedOnDisk):
        """
        Test that when a node is running, its downstream nodes are not locked, and their status is not updated.
        """
        import threading
        import time

        graph: Graph = graphSavedOnDisk
        node = graph.addNewNode("PluginANodeA")
        downstreamNode = graph.addNewNode("PluginANodeB")
        node.output.connectTo(downstreamNode.input)
        graph.save()

        self.checkNodeStatusAndLock(node, Status.NONE, False)
        self.checkNodeStatusAndLock(downstreamNode, Status.NONE, False)

        thread = threading.Thread(target=node.process, kwargs={"inCurrentEnv": True})
        thread.start()

        time.sleep(0.5)
        self.checkNodeStatusAndLock(node, Status.RUNNING, True)
        self.checkNodeStatusAndLock(downstreamNode, Status.NONE, False)

        thread.join()
        self.checkNodeStatusAndLock(node, Status.SUCCESS, False)
        self.checkNodeStatusAndLock(downstreamNode, Status.NONE, False)

    def test_upstreamLockDuringComputation(self, graphSavedOnDisk):
        """
        Test that when a node is running, its upstream nodes are locked and their status remains unchanged.
        """
        import threading
        import time

        graph: Graph = graphSavedOnDisk
        node = graph.addNewNode("PluginANodeA")
        downstreamNode = graph.addNewNode("PluginANodeB")
        node.output.connectTo(downstreamNode.input)
        graph.save()

        self.checkNodeStatusAndLock(node, Status.NONE, False)
        self.checkNodeStatusAndLock(downstreamNode, Status.NONE, False)

        node.process(inCurrentEnv=True)
        self.checkNodeStatusAndLock(node, Status.SUCCESS, False)
        self.checkNodeStatusAndLock(downstreamNode, Status.NONE, False)

        thread = threading.Thread(target=downstreamNode.process, kwargs={"inCurrentEnv": True})
        thread.start()
        time.sleep(0.5)
        self.checkNodeStatusAndLock(node, Status.SUCCESS, True)
        self.checkNodeStatusAndLock(downstreamNode, Status.RUNNING, True)

        thread.join()
        self.checkNodeStatusAndLock(node, Status.SUCCESS, False)
        self.checkNodeStatusAndLock(downstreamNode, Status.SUCCESS, False)

    def test_noDownstreamLockAfterParameterChange(self, graphSavedOnDisk):
        """
        Test that when a computed node's parameter is updated, the downstream node's status and lock are
        updated accordingly.
        """
        graph: Graph = graphSavedOnDisk
        node = graph.addNewNode("PluginANodeA")
        downstreamNode = graph.addNewNode("PluginANodeB")
        node.output.connectTo(downstreamNode.input)
        graph.save()

        self.checkNodeStatusAndLock(node, Status.NONE, False)
        self.checkNodeStatusAndLock(downstreamNode, Status.NONE, False)

        node.process(inCurrentEnv=True)
        downstreamNode.process(inCurrentEnv=True)

        self.checkNodeStatusAndLock(node, Status.SUCCESS, False)
        self.checkNodeStatusAndLock(downstreamNode, Status.SUCCESS, False)

        # Change a parameter on the upstream node and check that the downstream node's status is reset but not locked
        node.input.value = "path"
        self.checkNodeStatusAndLock(node, Status.NONE, False)
        self.checkNodeStatusAndLock(downstreamNode, Status.NONE, False)

    def test_noUpstreamLockAfterParameterChange(self, graphSavedOnDisk):
        """
        Test that when a computed node's parameter is updated, the upstream node's status and lock are not
        impacted.
        """
        graph: Graph = graphSavedOnDisk
        node = graph.addNewNode("PluginANodeA")
        downstreamNode = graph.addNewNode("PluginANodeB")
        node.output.connectTo(downstreamNode.input)
        graph.save()

        self.checkNodeStatusAndLock(node, Status.NONE, False)
        self.checkNodeStatusAndLock(downstreamNode, Status.NONE, False)

        node.process(inCurrentEnv=True)
        downstreamNode.process(inCurrentEnv=True)

        self.checkNodeStatusAndLock(node, Status.SUCCESS, False)
        self.checkNodeStatusAndLock(downstreamNode, Status.SUCCESS, False)

        # Disconnect the downstream node and check that the upstream node's status is not reset and that it is not locked
        downstreamNode.input.disconnectEdge()
        self.checkNodeStatusAndLock(node, Status.SUCCESS, False)
        self.checkNodeStatusAndLock(downstreamNode, Status.NONE, False)


class TestNode_SizeA(desc.BaseNode):
    __test__ = False
    size = desc.DynamicNodeSize("nbChunks")
    parallelization = desc.Parallelization(blockSize=1)
    inputs = [
        desc.IntParam(
            name="nbChunks",
            label="nbChunks",
            description="number of chunks",
            value=2,
        ),
        desc.File(
            name="nodeInput",
            label="Node Input",
            description="",
            value="",
        ),
    ]
    outputs = [
        desc.File(
            name='output',
            label='Output',
            description='Output',
            value=os.path.join("{nodeCacheFolder}"),
            commandLineGroup='',
        ),
    ]
    def processChunk(self, chunk):
        pass

class TestNode_SizeB(TestNode_SizeA):
    """ Inherit the linked node size but not parallelized """
    size = desc.DynamicNodeSize("nodeInput")
    parallelization = False

class TestNode_SizeC(TestNode_SizeA):
    """ Inherit the linked node size and parallelized """
    size = desc.DynamicNodeSize("nodeInput")
    parallelization = desc.Parallelization(blockSize=1)


class TestSizeUpdate:
    plugin = None

    @classmethod
    def setup_class(cls):
        registerNodeDesc(TestNode_SizeA)
        registerNodeDesc(TestNode_SizeB)
        registerNodeDesc(TestNode_SizeC)

    @classmethod
    def teardown_class(cls):
        unregisterNodeDesc(TestNode_SizeA)
        unregisterNodeDesc(TestNode_SizeB)
        unregisterNodeDesc(TestNode_SizeC)
    
    @staticmethod
    def checkNodeSizeAndStatus(node, nodeSize, nbChunks, status):
        assert node.size == nodeSize
        assert len(node._chunks) == nbChunks
        assert node.globalStatus == status.name

    def test_correctSizeUpdate(self, graphSavedOnDisk):
        graph: Graph = graphSavedOnDisk
        nodeA = graph.addNewNode("TestNode_SizeA")
        nodeB = graph.addNewNode("TestNode_SizeB")
        nodeA.output.connectTo(nodeB.nodeInput)
        nodeC = graph.addNewNode("TestNode_SizeC")
        nodeB.output.connectTo(nodeC.nodeInput)
        graph.save()
        
        # A
        self.checkNodeSizeAndStatus(nodeA, 0, 0, Status.NONE)
        nodeA.createChunks()
        nodeA.process(inCurrentEnv=True)
        self.checkNodeSizeAndStatus(nodeA, 2, 2, Status.SUCCESS)
        # B
        self.checkNodeSizeAndStatus(nodeB, 0, 1, Status.NONE)
        nodeB.createChunks()
        nodeB._updateNodeSize()
        nodeB.process(inCurrentEnv=True)
        self.checkNodeSizeAndStatus(nodeB, 2, 1, Status.SUCCESS)
        # C
        self.checkNodeSizeAndStatus(nodeC, 0, 0, Status.NONE)
        nodeC.createChunks()
        nodeC.process(inCurrentEnv=True)
        self.checkNodeSizeAndStatus(nodeC, 2, 2, Status.SUCCESS)


class TestPrePostProcess:
    """
    Test that preprocess and postprocess are correctly executed
    """
    @classmethod
    def setup_class(cls):
        registerNodeDesc(TestNodeD)
        registerNodeDesc(TestNodeE)

    @classmethod
    def teardown_class(cls):
        unregisterNodeDesc(TestNodeD)
        unregisterNodeDesc(TestNodeE)

    def test_status(self, graphSavedOnDisk):
        graph: Graph = graphSavedOnDisk
        node = graph.addNewNode(TestNodeD.__name__)
        graph.save()
        os.makedirs(node.internalFolder)
        
        # Check node
        assert len(node.chunks) == 1
        assert node.nodeDesc.hasPreprocess
        assert node.nodeDesc.hasPostprocess

        # Check status before
        assert node.globalStatus == Status.NONE.name
        assert node.chunks[0]._status.status == Status.NONE
        assert node._preprocessChunk._status.status == Status.NONE
        assert node._postprocessChunk._status.status == Status.NONE

        # Process
        node.preprocess(inCurrentEnv=True)
        node.process(inCurrentEnv=True)
        node.postprocess(inCurrentEnv=True)

        # Check status after
        assert node.globalStatus == Status.SUCCESS.name
        assert node.chunks[0]._status.status == Status.SUCCESS
        assert node._preprocessChunk._status.status == Status.SUCCESS
        assert node._postprocessChunk._status.status == Status.SUCCESS
    
    def test_failingpreprocess(self, graphSavedOnDisk):
        graph: Graph = graphSavedOnDisk
        node = graph.addNewNode(TestNodeE.__name__)
        graph.save()
        os.makedirs(node.internalFolder)

        # Check status before
        assert node.globalStatus == Status.NONE.name
        assert node._preprocessChunk._status.status == Status.NONE
        assert node.chunks[0]._status.status == Status.NONE

        # Process
        try:
            node.preprocess(inCurrentEnv=True)
        except Exception:
            pass
        else:
            raise RuntimeError
        # We execute the process because we know this will succeed and 
        # we want to test that the failed preprocess leads the global status
        node.process(inCurrentEnv=True)

        # Check status after
        assert node.globalStatus == Status.ERROR.name
        assert node.chunks[0]._status.status == Status.SUCCESS
        assert node._preprocessChunk._status.status == Status.ERROR
        
        # Cleanup: Close all logging handlers to release file locks (Windows fix)
        for handler in logging.root.handlers[:]:
            handler.close()
            logging.root.removeHandler(handler)
