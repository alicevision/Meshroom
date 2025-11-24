#!/usr/bin/env python
# coding:utf-8

import os
from pathlib import Path

from meshroom.core import pluginManager, loadClassesNodes
from meshroom.core.graph import Graph
from meshroom.core.plugins import Plugin

from .utils import registerNodeDesc


class TestNodeInfo:
    plugin = None

    @classmethod
    def setup_class(cls):
        cls.folder = os.path.join(os.path.dirname(__file__), "plugins", "meshroom")
        package = "pluginC"
        cls.plugin = Plugin(package, cls.folder)
        nodes = loadClassesNodes(cls.folder, package)
        for node in nodes:
            cls.plugin.addNodePlugin(node)
        pluginManager.addPlugin(cls.plugin)

    @classmethod
    def teardown_class(cls):
        for node in cls.plugin.nodes.values():
            pluginManager.unregisterNode(node)
        cls.plugin = None

    def test_loadedPlugin(self):
        assert len(pluginManager.getPlugins()) >= 1
        plugin = pluginManager.getPlugin("pluginC")
        assert plugin == self.plugin
        node = plugin.nodes["PluginCNodeA"]
        nodeType = node.nodeDescriptor

        g = Graph("")
        registerNodeDesc(nodeType)
        node = g.addNewNode(nodeType.__name__)

        nodeDocumentation = node.getDocumentation()
        assert nodeDocumentation == "PluginCNodeA"
        nodeInfo = {item["key"]: item["value"] for item in node.getNodeInfo()}
        assert nodeInfo["module"] == "pluginC.PluginCNodeA"
        pluginPath = os.path.join(self.folder, "pluginC", "PluginCNodeA.py")
        assert nodeInfo["modulePath"] == Path(pluginPath).as_posix()  # modulePath seems to follow Linux convention
        assert nodeInfo["author"] == "testAuthor"
        assert nodeInfo["license"] == "no-license"
        assert nodeInfo["version"] == "1.0"


class TestNodeVariables:
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

    def test_staticVariables(self):
        g = Graph("")

        for nodeName in self.plugin.nodes.keys():
            n = g.addNewNode(nodeName)
            assert nodeName == n._staticExpVars["nodeType"]
            assert n.sourceCodeFolder
            assert n.sourceCodeFolder == n._staticExpVars["nodeSourceCodeFolder"]

            self.plugin.nodes[nodeName].reload()

            assert nodeName == n._staticExpVars["nodeType"]
            assert n.sourceCodeFolder
            assert n.sourceCodeFolder == n._staticExpVars["nodeSourceCodeFolder"]

    def test_expVariables(self):
        g = Graph("")

        for nodeName in self.plugin.nodes.keys():
            n = g.addNewNode(nodeName)
            assert n._expVars["uid"] == n._uid
            assert n.internalFolder
            assert n.internalFolder == n._expVars["nodeCacheFolder"]

            self.plugin.nodes[nodeName].reload()

            assert n._expVars["uid"] == n._uid
            assert n.internalFolder
            assert n.internalFolder == n._expVars["nodeCacheFolder"]


class TestInitNode:
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

    def test_initNode(self):
        g = Graph("")

        node = g.addNewNode("PluginAInputInitNode")

        # Check that the init node is correctly detected
        initNodes = g.findInitNodes()
        assert len(initNodes) == 1 and node in initNodes

        # Check that the init node's initialize method has been set
        inputs = ["/path/to/file", "/path/to/file/2"]
        node.nodeDesc.initialize(node, inputs, None)
        assert node.input.value == inputs[0]
