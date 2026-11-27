# coding:utf-8

"""
This test aims to replicate toe process on node submission
"""

import os
import time
from sys import platform

from .utils import registerNodeDesc

import meshroom
from meshroom.core import pluginManager, meshroomFolder
from meshroom.core.graph import Graph
from meshroom.core.node import Node, Status
from meshroom.core.submitter import jobManager
from meshroom.core.submitter import OrderedTask, OrderedTasks, OrderedTaskType
from meshroom.submitters.localFarm.localFarmSubmitter import LocalFarmSubmitter, LocalFarmJob

from localfarm.localFarmLauncher import FarmLauncher

import logging
from meshroom.core.submitter import logger
logger.setLevel(logging.DEBUG)


IS_LINUX = (platform == "linux" or platform == "linux2")


def get_submitter() -> LocalFarmSubmitter:
    for sName, s in meshroom.core.submitters.items():
        if sName == "LocalFarm":
            return s
    raise RuntimeError("LocalFarm submitter not found")


def getJobEnv(submittersAvailable=False):
    """
    Required to have meshroom recognize the test plugin.

    Args:
        submittersAvailable (bool): whether the farm tasks can find the LocalFarm submitter. If they can,
            meshroom_createChunks creates a farm task per chunk; otherwise, it computes the chunks itself.
    """
    pluginFolder = os.path.join(os.path.dirname(__file__), "plugins", "pluginSubmitter")
    env = {
        "MESHROOM_PLUGINS_PATH": pluginFolder,
        # Disable all rez variables that could lead to using rez in the test env
        "REZ_RESOLVE": "",
        "REZ_USED_RESOLVE": "",
        "REZ_BIN": "",
        "REZ_PACKAGES_ROOT": "",
        "REZ_REQUEST": "",
        "REZ_USED_REQUEST": "",
        "REZ_MESHROOM_VERSION": ""
    }
    if submittersAvailable:
        env["MESHROOM_SUBMITTERS_PATH"] = os.path.join(meshroomFolder, "submitters")
    return env


def getChunkTaskIterations(tasks):
    """ Get the sorted iterations of the farm tasks that compute a single chunk. """
    return sorted(t["metadata"]["iteration"] for t in tasks if isinstance(t["metadata"].get("iteration"), int))


def checkTask(task, taskType, nbDependencies):
    """ Check a task has the correct type and number of dependencies """
    assert task.taskType == taskType
    assert len(task.dependencies) == nbDependencies


def waitForNodeCompletion(job: LocalFarmJob, node: Node, timeout=30):
    """
    Wait for a node to complete processing
    """
    print(f"Waiting for node {node.name} to complete...")
    startTime = time.time()
    while True:
        time.sleep(1)
        if time.time() - startTime > timeout:
            raise TimeoutError((
                f"Node {node.name} did not complete within {timeout} seconds. "
                "You might want to increase the timeout duration in the test "
                "or check why the test is taking more time."
            ))
        # Check for job error
        err = job.getJobErrors()
        if err:
            raise RuntimeError(f"Job encountered an error: {err}")
        # Check that all tasks are finished
        for task in job.localfarmTasks.values():
            if task.get("status") not in (Status.NONE.name, Status.SUCCESS.name, Status.STOPPED.name, Status.ERROR.name):
                break
        else:
            # All the tasks are finished
            node.updateStatusFromCache()
            nodeStatus = node.getGlobalStatus()
            print(f"Node status switched to {nodeStatus}")
            break


def processSubmit(node: Node, graph, tmp_path, jobEnv=None):
    """
    Actual function that test the submit process

    Returns:
        list[dict]: the tasks of the farm job once the node is computed.
    """
    # Save graph
    tmp_path = str(tmp_path)
    graph.save(os.path.join(tmp_path, "graph.mg"))
    # Prepare all chunks
    node.initStatusOnSubmit()
    # Start farm
    farmLauncher = FarmLauncher(tmp_path)
    farmLauncher.start()
    time.sleep(1)
    error = None
    tasks = []
    try:
        print(f"submit {node}")
        submitter = get_submitter()
        submitter.disabled_rez = True
        submitter.setFarmPath(tmp_path)
        submitter.setJobEnv(jobEnv or getJobEnv())
        nodesToProcess, edgesToProcess = [node], []
        # Update nodes status
        for node in nodesToProcess:
            node.initStatusOnSubmit()
        # Update monitored to make sure meshroom knows when task status change
        graph.updateMonitoredFiles()
        assert node.getGlobalStatus() == Status.SUBMITTED
        res = submitter.submit(nodesToProcess, edgesToProcess, graph.filepath, submitLabel="TestSubmit")
        assert res is not None, "Submitter returned no job"
        assert res.__class__.__name__ == "LocalFarmJob", "Submitted job is not a LocalFarmJob"
        jobManager.addJob(res, nodesToProcess)
        waitForNodeCompletion(res, node)
        tasks = list(res.localfarmTasks.values())
    except Exception as e:
        error = e
    finally:
        farmLauncher.status(allInfo=True)
        farmLauncher.stop()
    if error:
        raise error
    else:
        farmLauncher.clean()
    return tasks


class TestNodeSubmit:
    __test__ = IS_LINUX

    @classmethod
    def setup_class(cls):
        localFarmFolder = os.path.join(meshroomFolder, "submitters", "localFarm")
        pluginManager.addPluginFromBuiltInFolder("localFarm", localFarmFolder)
        submitterProvider = pluginManager.getSubmitterProvider("LocalFarm")
        meshroom.core.submitters[submitterProvider.name] = submitterProvider.instance

        cls.folder = os.path.join(os.path.dirname(__file__), "plugins", "pluginSubmitter")
        pluginManager.addPluginFromBuiltInFolder("pluginSubmitter", cls.folder)

    @classmethod
    def teardown_class(cls):
        plugin = pluginManager.getPlugin("pluginSubmitter")
        if plugin:
            pluginManager.removePlugin(plugin)

    def registerNode(self, name):
        plugin = pluginManager.getPlugin("pluginSubmitter")
        node = plugin.nodeDescProviders[name]
        nodeType = node.nodeDescClass
        registerNodeDesc(nodeType)
        return nodeType.__name__

    def addNewNode(self, graph, name, nodeParams=None):
        nodeTypeName = self.registerNode(name)
        nodeParams = nodeParams or {}
        node = graph.addNewNode(nodeTypeName, **nodeParams)
        return node

    def test_simpleOrderTasks(self):
        """ Here is the example we use for testing :

                     *" [A chk_0] "*
        [phd start_A]               [phd end_A] - [phd root]
                     *_ [A chk_1] _*

        phd=placeholder (no command/process executed)
        chk=chunk
        """
        graph = Graph("")
        nodeA = self.addNewNode(graph, "PluginSubmitterA1", nodeParams={})
        nodes, edges = graph.dfsOnFinish(startNodes=[nodeA])
        orderedTasks = OrderedTasks(nodes, edges)
        rootTask = orderedTasks.rootTask
        checkTask(rootTask, OrderedTaskType.PLACEHOLDER, 1)
        task: OrderedTask = rootTask.dependencies[0]
        checkTask(task, OrderedTaskType.PLACEHOLDER, 2)
        task_0: OrderedTask = task.dependencies[0]
        task_1: OrderedTask = task.dependencies[1]
        checkTask(task_0, OrderedTaskType.CHUNK, 1)
        checkTask(task_1, OrderedTaskType.CHUNK, 1)
        task: OrderedTask = task_0.dependencies[0]
        checkTask(task, OrderedTaskType.PLACEHOLDER, 0)

    def test_complexOrderTasks(self):
        """ Here is the example we use for testing :

        [A_0 chk] "*.             *" [B chk_0] "*
                     [phd start_B]               [B post] - [C pre] - [C exp] - [C post] - [phd root]
        [A_1 chk] _*"             *_ [B chk_1] _*

        phd=placeholder (no command/process executed)
        chk=chunk
        exp=expand
        """

        # First do a simple test

        # Now do a more complex test
        graph = Graph("")
        # Add nodes
        nodeA0 = self.addNewNode(graph, "PluginSubmitterA", nodeParams={})
        nodeA1 = self.addNewNode(graph, "PluginSubmitterA", nodeParams={})
        nodeB = self.addNewNode(graph, "PluginSubmitterB", nodeParams={"inputs": [nodeA0.output, nodeA1.output]})
        nodeC = self.addNewNode(graph, "PluginSubmitterC", nodeParams={"inputs": [nodeB.output]})
        # Order tasks
        nodes, edges = graph.dfsOnFinish(startNodes=[nodeC])
        orderedTasks = OrderedTasks(nodes, edges)
        # === Test result ===
        # root
        rootTask = orderedTasks.rootTask
        checkTask(rootTask, OrderedTaskType.PLACEHOLDER, 1)
        # C (post)
        task: OrderedTask = rootTask.dependencies[0]
        checkTask(task, OrderedTaskType.POSTPROCESS, 1)
        # C (expand)
        task: OrderedTask = task.dependencies[0]
        checkTask(task, OrderedTaskType.EXPANDING, 1)
        # C (pre)
        task: OrderedTask = task.dependencies[0]
        checkTask(task, OrderedTaskType.PREPROCESS, 1)
        # B (post)
        task: OrderedTask = task.dependencies[0]
        checkTask(task, OrderedTaskType.POSTPROCESS, 2)
        # B (chunks)
        task_0: OrderedTask = task.dependencies[0]
        task_1: OrderedTask = task.dependencies[1]
        checkTask(task_0, OrderedTaskType.CHUNK, 1)
        checkTask(task_1, OrderedTaskType.CHUNK, 1)
        assert (task_0.iteration, task_1.iteration) == (0, 1)
        assert task_0.dependencies[0] == task_1.dependencies[0]
        # B (pre)
        task: OrderedTask = task_0.dependencies[0]
        checkTask(task, OrderedTaskType.PLACEHOLDER, 2)
        # A
        # No post process, no preprocess, 1 chunk = no placeholder pre/post either
        # A (chunks)
        task_A0: OrderedTask = task.dependencies[0]
        checkTask(task_A0, OrderedTaskType.CHUNK, 0)
        assert task_A0.iteration == -1
        task_A1: OrderedTask = task.dependencies[1]
        checkTask(task_A1, OrderedTaskType.CHUNK, 0)
        assert task_A1.iteration == -1

    def test_submitNoParallel(self, tmp_path):
        graph = Graph("")
        graph._cacheDir = os.path.join(tmp_path, "cache")
        node = self.addNewNode(graph, "PluginSubmitterA")
        # Submit
        processSubmit(node, graph, tmp_path)

    def test_submitStaticSize(self, tmp_path):
        graph = Graph("")
        graph._cacheDir = os.path.join(tmp_path, "cache")
        node = self.addNewNode(graph, "PluginSubmitterB")
        # Submit
        processSubmit(node, graph, tmp_path)

    def test_submitDynamicSizeChunkTasks(self, tmp_path):
        """ meshroom_createChunks finds the submitter and creates a farm task for each chunk. """
        graph = Graph("")
        graph._cacheDir = os.path.join(tmp_path, "cache")
        node = self.addNewNode(graph, "PluginSubmitterC", {"nbChunks": 3})
        # Submit
        tasks = processSubmit(node, graph, tmp_path, getJobEnv(submittersAvailable=True))
        assert getChunkTaskIterations(tasks) == [0, 1, 2]
        assert node.getGlobalStatus() == Status.SUCCESS

    def test_submitDynamicSizeFallback(self, tmp_path):
        """ meshroom_createChunks cannot find the submitter and computes all the chunks itself. """
        graph = Graph("")
        graph._cacheDir = os.path.join(tmp_path, "cache")
        node = self.addNewNode(graph, "PluginSubmitterC", {"nbChunks": 3})
        # Submit
        tasks = processSubmit(node, graph, tmp_path, getJobEnv(submittersAvailable=False))
        assert getChunkTaskIterations(tasks) == []
        assert node.getGlobalStatus() == Status.SUCCESS
        assert len(node.chunks) == 3
