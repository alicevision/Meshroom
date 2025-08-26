#!/usr/bin/env python
# coding:utf-8

import os
from pathlib import Path

from meshroom.core import pluginManager, loadClassesNodes
from meshroom.core.plugins import Plugin
from meshroom.core import pluginManager
from meshroom.core import pluginManager
from meshroom.core.graph import Graph

from .utils import registerNodeDesc


class TestNodeInfos:
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
        nodeInfos = {item["key"]: item["value"] for item in node.getNodeInfos()}
        assert nodeInfos["module"] == "pluginC.PluginCNodeA"
        plugin_path = os.path.join(self.folder, "pluginC", "PluginCNodeA.py")
        assert nodeInfos["modulePath"] == Path(plugin_path).as_posix()  # modulePath seems to follow linux convention
        assert nodeInfos["author"] == "testAuthor"
        assert nodeInfos["license"] == "no-license"
        assert nodeInfos["version"] == "1.0"
