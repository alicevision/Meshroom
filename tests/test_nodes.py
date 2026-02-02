#!/usr/bin/env python
# coding:utf-8

import os
from pathlib import Path
import tempfile

from meshroom.core import pluginManager, loadClassesNodes, initNodes
from meshroom.core.graph import Graph, loadGraph
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


class TestBackdropNode:
    loadedPlugins = pluginManager.getPlugins()

    @classmethod
    def setup_class(cls):
        initNodes()

    @classmethod
    def teardown_class(cls):
        for plugin in pluginManager.getPlugins():
            if plugin not in cls.loadedPlugins:
                for node in plugin.nodes.values():
                    pluginManager.unregisterNode(node)
                pluginManager.removePlugin(plugin)

    def test_backdropNode(self):
        """ Test that a backdrop node can be added to a graph with its expected default values. """
        g = Graph("Default Backdrop node")
        backdrop = g.addNewNode("Backdrop")

        # Check that the default values for backdrop are as expected
        assert backdrop is not None
        assert backdrop.nodeWidth == 600
        assert backdrop.nodeHeight == 400
        assert backdrop.fontSize == 12
        assert backdrop.fontColor == ""
        assert backdrop.color == ""
        assert backdrop.comment == ""

        # Add a non-backdrop node and check that its default values are not backdrop's ones
        node = g.addNewNode("CopyFiles")
        assert node is not None
        assert node.nodeWidth == 0
        assert node.nodeHeight == 0
        assert node.fontSize == 0
        assert node.fontColor == ""
        assert node.color == ""
        assert node.comment == ""

    def test_backdropNode_customAttributes(self):
        """ Test that a backdrop node's attributes can be correctly updated. """
        g = Graph("Backdrop node with custom values")
        backdrop = g.addNewNode("Backdrop")

        # Set custom values for backdrop and assert the properties are correctly updated
        width = backdrop.internalAttribute("nodeWidth")
        width.value = 400
        assert backdrop.nodeWidth == 400

        height = backdrop.internalAttribute("nodeHeight")
        height.value = 200
        assert backdrop.nodeHeight == 200

        fontSize = backdrop.internalAttribute("fontSize")
        fontSize.value = 10
        assert backdrop.fontSize == 10

        fontColor = backdrop.internalAttribute("fontColor")
        fontColor.value = "#00FF00"
        assert backdrop.fontColor == "#00FF00"

        color = backdrop.internalAttribute("color")
        color.value = "#FF0000"
        assert backdrop.color == "#FF0000"

        comment = backdrop.internalAttribute("comment")
        comment.value = "hello world"
        assert backdrop.comment == "hello world"

    def test_backdropNode_defaultSerialization(self):
        """ Test that a backdrop node with default values is correctly serialized and deserialized. """
        g = Graph("Backdrop node default serialization")
        backdrop = g.addNewNode("Backdrop")

        # Save the graph in a file
        graphFile = os.path.join(tempfile.mkdtemp(), "test_backdrop_serialization.mg")
        g.save(graphFile)

        # Reload the graph and check the values for the backdrop node are the default ones
        g = loadGraph(graphFile)
        backdrop = g.node("Backdrop_1")
        assert backdrop is not None
        assert backdrop.nodeWidth == 600
        assert backdrop.nodeHeight == 400
        assert backdrop.fontSize == 12
        assert backdrop.fontColor == ""
        assert backdrop.color == ""
        assert backdrop.comment == ""

    def test_backdropNode_customSerialization(self):
        """ Test that a backdrop node with custom values is correctly serialized and deserialized. """
        g = Graph("Backdrop node custom serialization")
        backdrop = g.addNewNode("Backdrop")

        # Set custom values for backdrop
        width = backdrop.internalAttribute("nodeWidth")
        width.value = 400
        height = backdrop.internalAttribute("nodeHeight")
        height.value = 200
        fontSize = backdrop.internalAttribute("fontSize")
        fontSize.value = 10
        fontColor = backdrop.internalAttribute("fontColor")
        fontColor.value = "#00FF00"
        color = backdrop.internalAttribute("color")
        color.value = "#FF0000"
        comment = backdrop.internalAttribute("comment")
        comment.value = "hello world"

        # Save the graph in a file
        graphFile = os.path.join(tempfile.mkdtemp(), "test_backdrop_serialization.mg")
        g.save(graphFile)

        # Reload the graph and check the values for the backdrop node are the default ones
        g = loadGraph(graphFile)
        backdrop = g.node("Backdrop_1")
        assert backdrop is not None
        assert backdrop.nodeWidth == 400
        assert backdrop.nodeHeight == 200
        assert backdrop.fontSize == 10
        assert backdrop.fontColor == "#00FF00"
        assert backdrop.color == "#FF0000"
        assert backdrop.comment == "hello world"
