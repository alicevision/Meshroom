# coding:utf-8

"""
This test aims to replicate toe process on node submission
"""

import os
import time
from sys import platform

from .utils import registerNodeDesc

import meshroom
from meshroom.core import pluginManager, loadClassesNodes, loadSubmitters, registerSubmitter, meshroomFolder
from meshroom.core.graph import Graph
from meshroom.core.plugins import Plugin
from meshroom.core.node import Node, Status
from meshroom.core.submitter import BaseSubmitter
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


def getJobEnv():
    """ Required to have meshroom recognize plugins that were created here """
    pluginFolder = os.path.join(os.path.dirname(__file__), "plugins")
    return {
        "MESHROOM_PLUGINS_PATH": pluginFolder
    }


def waitForNodeCompletion(job: LocalFarmJob, node: Node, timeout=10):
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


def processSubmit(node: Node, graph, tmp_path):
    """
    Actual function that test the submit process
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
    try:
        print(f"submit {node}")
        submitter = get_submitter()
        submitter.disabled_rez = True
        submitter.setFarmPath(tmp_path)
        submitter.setJobEnv(getJobEnv())
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
    except Exception as e:
        error = e
    finally:
        farmLauncher.status(allInfo=True)
        farmLauncher.stop()
    if error:
        raise error
    else:
        farmLauncher.clean()


class TestNodeSubmit:
    __test__ = IS_LINUX

    @classmethod
    def setup_class(cls):
        submittersFolder = os.path.join(meshroomFolder, "submitters")
        submitters = loadSubmitters(submittersFolder, "localFarm")
        for submitter in submitters:
            registerSubmitter(submitter())

        cls.folder = os.path.join(os.path.dirname(__file__), "plugins", "meshroom")
        package = "pluginSubmitter"
        cls.plugin = Plugin(package, cls.folder)
        nodes = loadClassesNodes(cls.folder, package)
        for node in nodes:
            cls.plugin.addNodePlugin(node)
        pluginManager.addPlugin(cls.plugin)

    @classmethod
    def teardown_class(cls):
        for node in cls.plugin.nodes.values():
            pluginManager.unregisterNode(node)
        pluginManager.removePlugin(cls.plugin)
        cls.plugin = None

    def registerNode(self, name):
        plugin = pluginManager.getPlugin("pluginSubmitter")
        node = plugin.nodes[name]
        nodeType = node.nodeDescriptor
        registerNodeDesc(nodeType)
        return nodeType.__name__

    def addNewNode(self, graph, name, nodeParams=None):
        nodeTypeName = self.registerNode(name)
        nodeParams = nodeParams or {}
        node = graph.addNewNode(nodeTypeName, **nodeParams)
        return node

    def test_orderTasks(self):
        """ Here is the example we use for testing :
                                                             *" [B chk_0] "* 
        [phd start_A] - [A chk] - [phd end_A] - [phd start_B]               [B post] - [C pre] - [C exp] - [C post] - [phd root]
                                                             *_ [B chk_1] _* 
        phd=placeholder (no command/process executed)
        chk=chunk
        exp=expand
        """
        graph = Graph("")
        # Add nodes
        nodeA = self.addNewNode(graph, "PluginSubmitter"+"A", nodeParams={})
        nodeB = self.addNewNode(graph, "PluginSubmitter"+"B", nodeParams={"inputs": [nodeA.output]})
        nodeC = self.addNewNode(graph, "PluginSubmitter"+"C", nodeParams={"inputs": [nodeB.output]})
        # Order tasks
        nodes, edges = graph.dfsOnFinish(startNodes=[nodeC])
        orderedTasks = OrderedTasks(nodes, edges)
        # === Test result ===
        def checkTask(task, taskType, nbDependencies):
            assert task.taskType == taskType
            assert len(task.dependencies) == nbDependencies
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
        checkTask(task, OrderedTaskType.PLACEHOLDER, 1)
        # A (post)
        task: OrderedTask = task.dependencies[0]
        checkTask(task, OrderedTaskType.PLACEHOLDER, 1)
        # A (chunks)
        task: OrderedTask = task.dependencies[0]
        checkTask(task, OrderedTaskType.CHUNK, 1)
        assert task.iteration == -1
        # A (pre)
        task: OrderedTask = task.dependencies[0]
        checkTask(task, OrderedTaskType.PLACEHOLDER, 0)

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

    def test_submitDynamicSize(self, tmp_path):
        graph = Graph("")
        graph._cacheDir = os.path.join(tmp_path, "cache")
        node = self.addNewNode(graph, "PluginSubmitterC")
        # Submit
        processSubmit(node, graph, tmp_path)
