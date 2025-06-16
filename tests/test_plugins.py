# coding:utf-8

from meshroom.core import pluginManager, loadClassesNodes
from meshroom.core.plugins import NodePluginStatus, Plugin

import os
import time


class TestPluginWithValidNodesOnly:
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
        cls.plugin = None

    def test_loadedPlugin(self):
        # Assert that there are loaded plugins, and that "pluginA" is one of them
        assert len(pluginManager.getPlugins()) >= 1
        plugin = pluginManager.getPlugin("pluginA")
        assert plugin == self.plugin
        assert str(plugin.path) == os.path.join(os.path.dirname(__file__), "plugins", "meshroom")

        # Assert that the nodes of pluginA have been successfully registered
        assert len(pluginManager.getRegisteredNodePlugins()) >= 2
        for nodeName, nodePlugin in plugin.nodes.items():
            assert nodePlugin.status == NodePluginStatus.LOADED
            assert pluginManager.isRegistered(nodeName)

        # Assert the template has been loaded
        assert len(plugin.templates) == 1
        name = list(plugin.templates.keys())[0]
        assert name == "sharedTemplate"
        assert plugin.templates[name] == os.path.join(str(plugin.path), "sharedTemplate.mg")

    def test_unloadPlugin(self):
        plugin = pluginManager.getPlugin("pluginA")
        assert plugin == self.plugin

        # Unload the plugin without unregistering the nodes
        pluginManager.removePlugin(plugin, unregisterNodePlugins=False)

        # Assert the plugin is not loaded anymore
        assert pluginManager.getPlugin(plugin.name) is None

        # Assert the nodes are still registered and belong to an unloaded plugin
        for nodeName, nodePlugin in plugin.nodes.items():
            assert nodePlugin.status == NodePluginStatus.LOADED
            assert pluginManager.isRegistered(nodeName)
            assert pluginManager.belongsToPlugin(nodeName) is None

        # Re-add the plugin
        pluginManager.addPlugin(plugin, registerNodePlugins=False)
        assert pluginManager.getPlugin(plugin.name)

        # Unload the plugin with a full unregistration of the nodes
        pluginManager.removePlugin(plugin)

        # Assert the plugin is not loaded anymore
        assert pluginManager.getPlugin(plugin.name) is None

        # Assert the nodes have been successfully unregistered
        for nodeName, nodePlugin in plugin.nodes.items():
            assert nodePlugin.status == NodePluginStatus.NOT_LOADED
            assert not pluginManager.isRegistered(nodeName)

        # Re-add the plugin and re-register the nodes
        pluginManager.addPlugin(plugin)
        assert pluginManager.getPlugin(plugin.name)
        for nodeName, nodePlugin in plugin.nodes.items():
            assert nodePlugin.status == NodePluginStatus.LOADED
            assert pluginManager.isRegistered(nodeName)

    def test_updateRegisteredNodes(self):
        nbRegisteredNodes = len(pluginManager.getRegisteredNodePlugins())
        plugin = pluginManager.getPlugin("pluginA")
        assert plugin == self.plugin
        nodeA = pluginManager.getRegisteredNodePlugin("PluginANodeA")
        nodeAName = nodeA.nodeDescriptor.__name__

        # Unregister a node
        assert nodeA
        pluginManager.unregisterNode(nodeA)

        # Check that the node has been fully unregistered:
        #   - its status is "NOT_LOADED"
        #   - it is still part of pluginA
        #   - it is not in the list of registered plugins anymore (and returns None when requested)
        assert nodeA.status == NodePluginStatus.NOT_LOADED
        assert plugin.containsNodePlugin(nodeAName)
        assert nodeA.plugin == plugin

        assert pluginManager.getRegisteredNodePlugin(nodeAName) is None
        assert nodeAName not in pluginManager.getRegisteredNodePlugins()
        assert len(pluginManager.getRegisteredNodePlugins()) == nbRegisteredNodes - 1

        # Re-register the node
        pluginManager.registerNode(nodeA)

        assert nodeA.status == NodePluginStatus.LOADED
        assert pluginManager.getRegisteredNodePlugin(nodeAName)
        assert len(pluginManager.getRegisteredNodePlugins()) == nbRegisteredNodes


class TestPluginWithInvalidNodes:
    plugin = None

    @classmethod
    def setup_class(cls):
        folder = os.path.join(os.path.dirname(__file__), "plugins", "meshroom")
        package = "pluginB"
        cls.plugin = Plugin(package, folder)
        nodes = loadClassesNodes(folder, package)
        for node in nodes:
            cls.plugin.addNodePlugin(node)
        pluginManager.addPlugin(cls.plugin)

    @classmethod
    def teardown_class(cls):
        for node in cls.plugin.nodes.values():
            pluginManager.unregisterNode(node)
        cls.plugin = None

    def test_loadedPlugin(self):
        # Assert that there are loaded plugins, and that "pluginB" is one of them
        assert len(pluginManager.getPlugins()) >= 1
        plugin = pluginManager.getPlugin("pluginB")
        assert plugin == self.plugin
        assert str(plugin.path) == os.path.join(os.path.dirname(__file__), "plugins", "meshroom")

        # Assert that PluginBNodeA is successfully registered
        assert pluginManager.isRegistered("PluginBNodeA")
        assert plugin.nodes["PluginBNodeA"].status == NodePluginStatus.LOADED
        assert plugin.nodes["PluginBNodeA"].plugin == plugin

        # Assert that PluginBNodeB has not been registered (description error)
        assert not pluginManager.isRegistered("PluginBNodeB")
        assert plugin.nodes["PluginBNodeB"].status == NodePluginStatus.DESC_ERROR
        assert plugin.nodes["PluginBNodeB"].plugin == plugin

        # Assert the template has been loaded
        assert len(plugin.templates) == 1
        name = list(plugin.templates.keys())[0]
        assert name == "sharedTemplate"
        assert plugin.templates[name] == os.path.join(str(plugin.path), "sharedTemplate.mg")

    def test_reloadNodePlugin(self):
        plugin = pluginManager.getPlugin("pluginB")
        assert plugin == self.plugin
        node = plugin.nodes["PluginBNodeB"]
        nodeName = node.nodeDescriptor.__name__

        # Check that the node has not been registered
        assert node.status == NodePluginStatus.DESC_ERROR
        assert not pluginManager.isRegistered(nodeName)

        # Check that the node cannot be registered
        pluginManager.registerNode(node)
        assert not pluginManager.isRegistered(nodeName)

        # Replace directly in the node file the line that fails the validation
        # on the description with a line that will pass
        originalFileContent = None
        with open(node.path, "r") as f:
            originalFileContent = f.read()

        replaceFileContent = originalFileContent.replace('"not an integer"', '1')
        with open(node.path, "w") as f:
            f.write(replaceFileContent)

        # Reload the node and assert it is valid
        node.reload()
        assert node.status == NodePluginStatus.NOT_LOADED

        # Attempt to register node plugin
        pluginManager.registerNode(node)
        assert pluginManager.isRegistered(nodeName)

        # Reload the node again without any change
        node.reload()
        assert pluginManager.isRegistered(nodeName)

        # Hack to ensure that the timestamp of the file will be different after being rewritten
        # Without it, on some systems, the operation is too fast and the timestamp does not change,
        # cause the test to fail
        time.sleep(0.1)

        # Restore the node file to its original state (with a description error)
        with open(node.path, "w") as f:
            f.write(originalFileContent)

        timestampOr2 = os.path.getmtime(node.path)
        print(f"New timestamp: {timestampOr2}")
        print(os.stat(node.path))

        # Reload the node and assert it is invalid while still registered
        node.reload()
        assert node.status == NodePluginStatus.DESC_ERROR
        assert pluginManager.isRegistered(nodeName)

        # Unregister it
        pluginManager.unregisterNode(node)
        assert node.status == NodePluginStatus.DESC_ERROR  # Not NOT_LOADED
        assert not pluginManager.isRegistered(nodeName)
