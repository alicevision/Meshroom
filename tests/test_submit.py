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
from meshroom.submitters.localFarmSubmitter import LocalFarmSubmitter, LocalFarmJob

from localfarm.localFarmLauncher import FarmLauncher


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


def waitForNodeCompletion(job: LocalFarmJob, node: Node, timeout=25):
    """
    Wait for a node to complete processing
    """
    print(f"Waiting for node {node.name} to complete...")
    startTime = time.time()
    while True:
        node.updateStatusFromCache()
        nodeStatus = node.getGlobalStatus()
        if nodeStatus not in (Status.SUBMITTED, Status.RUNNING):
            print(f"Node status switched to {nodeStatus}")
            return
        # Check for job error
        err = job.getJobErrors()
        if err:
            raise RuntimeError(f"Job encountered an error: {err}")
        if time.time() - startTime > timeout:
            raise TimeoutError(f"Node {node.name} did not complete within {timeout} seconds")
        time.sleep(1)

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
        farmLauncher.stop()
    if error:
        raise error
    else:
        farmLauncher.clean()


class TestNodeSubmit:
    __test__ = IS_LINUX

    @classmethod
    def setup_class(cls):
        # meshroom.core.initSubmitters()
        submitters = loadSubmitters(meshroomFolder, "submitters")
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

    def addNewNode(self, graph, name, nodeParams):
        nodeTypeName = self.registerNode(name)
        if nodeParams:
            node = graph.addNewNode(nodeTypeName, **nodeParams)
        else:
            node = graph.addNewNode(nodeTypeName)
        return node

    def test_buildTaskGraph(self):
        graph = Graph("")
        # Add nodes
        nodeA = self.addNewNode(graph, "PluginSubmitter"+"A"+"PrePost", nodeParams={})
        nodeB = self.addNewNode(graph, "PluginSubmitter"+"B"+"PrePost", nodeParams={"inputs": [nodeA.output]})
        nodeC = self.addNewNode(graph, "PluginSubmitter"+"C"+"PrePost", nodeParams={"inputs": [nodeB.output]})
        # Submit
        submitter = get_submitter()
        nodes, edges = graph.dfsOnFinish(startNodes=[nodeC])
        print(nodes, edges)
        res = submitter.submit(nodes, edges, "")
        print("res", res)

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
