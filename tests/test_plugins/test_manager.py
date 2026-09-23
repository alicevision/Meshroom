# coding:utf-8

from meshroom.core import pluginManager
from meshroom.core.desc.node import NodeVersionType
from meshroom.core.plugins.base import NodeDescProviderStatus
from ..utils import overrideOsEnvironmentVariables, registeredPlugin

import os
import time

# The folder of the test plugins.
pluginsFolder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugins")


class TestPluginWithValidNodesOnly:

    @classmethod
    def setup_class(cls):
        cls.folder = os.path.join(pluginsFolder, "pluginA")
        pluginManager.addPluginFromPath("pluginA", cls.folder)

    @classmethod
    def teardown_class(cls):
        plugin = pluginManager.getPlugin("pluginA")
        if plugin:
            pluginManager.removePlugin(plugin)

    def test_getPlugin(self):
        # Assert that there are loaded plugins, and that "pluginA" is one of them
        assert len(pluginManager.getPlugins()) >= 1
        # Get with name
        plugin = pluginManager.getPlugin("pluginA")
        assert plugin
        assert plugin.name == "pluginA"
        # Check path too
        assert str(plugin.hostPath) == os.path.join(pluginsFolder, "pluginA", "meshroom")

    def test_loadedPlugin(self):
        # Assert that there are loaded plugins, and that "pluginA" is one of them
        plugin = pluginManager.getPlugin("pluginA")
        # Assert that the nodes of pluginA have been successfully registered
        assert len(pluginManager.getNodeDescProviders()) >= 2
        for nodeName, nodeDescProvider in plugin.nodeDescProviders.items():
            assert nodeDescProvider.status == NodeDescProviderStatus.VALID
            assert pluginManager.isNodeDescRegistered(nodeName)

        # Assert the template has been loaded
        assert len(plugin.templates) == 1
        name = list(plugin.templates.keys())[0]
        assert name == "sharedTemplate"
        assert plugin.templates[name] == os.path.join(str(plugin.hostPath), "sharedTemplate.mg")

    def test_removePlugin(self):
        plugin = pluginManager.getPlugin("pluginA")
        assert plugin

        # Remove the plugin
        pluginManager.removePlugin(plugin)

        # Assert the plugin is not loaded anymore
        assert pluginManager.getPlugin(plugin.name) is None

        # Assert the nodes have been successfully unregistered
        for nodeName, nodeDescProvider in plugin.nodeDescProviders.items():
            assert not pluginManager.isNodeDescRegistered(nodeName)

        # Re-load the plugin and re-register the nodes
        pluginManager.addPluginFromPath("pluginA", self.folder)

        # Assert the nodes have been successfully registered
        assert pluginManager.getPlugin(plugin.name)
        for nodeName, nodeDescProvider in plugin.nodeDescProviders.items():
            assert pluginManager.isNodeDescRegistered(nodeName)


class TestPluginWithInvalidNodes:

    @classmethod
    def setup_class(cls):
        cls.folder = os.path.join(pluginsFolder, "pluginB")
        pluginManager.addPluginFromPath("pluginB", cls.folder)

    @classmethod
    def teardown_class(cls):
        plugin = pluginManager.getPlugin("pluginB")
        if plugin:
            pluginManager.removePlugin(plugin)

    def test_loadedPlugin(self):
        # Assert that there are loaded plugins, and that "pluginB" is one of them
        assert len(pluginManager.getPlugins()) >= 1
        plugin = pluginManager.getPlugin("pluginB")
        assert plugin
        assert str(plugin.hostPath) == os.path.join(pluginsFolder, "pluginB", "meshroom")

        # Assert that PluginBNodeA is successfully registered
        assert pluginManager.isNodeDescRegistered("PluginBNodeA")
        assert plugin.nodeDescProviders["PluginBNodeA"].status == NodeDescProviderStatus.VALID
        assert plugin.nodeDescProviders["PluginBNodeA"].plugin == plugin

        # Assert that PluginBNodeB has not been registered (description error)
        assert not pluginManager.isNodeDescRegistered("PluginBNodeB")
        assert plugin.nodeDescProviders["PluginBNodeB"].status == NodeDescProviderStatus.DESC_ERROR
        assert plugin.nodeDescProviders["PluginBNodeB"].plugin == plugin

        # Assert no template has been loaded
        assert len(plugin.templates) == 0

    def test_reloadNodeDescProviderInvalidDescrpition(self):
        plugin = pluginManager.getPlugin("pluginB")
        assert plugin
        nodeDescProvider = plugin.nodeDescProviders["PluginBNodeB"]

        # Check that the node has not been registered
        assert nodeDescProvider.status == NodeDescProviderStatus.DESC_ERROR
        assert not pluginManager.isNodeDescRegistered(nodeDescProvider.name)

        # Replace directly in the node file the line that fails the validation
        # on the description with a line that will pass
        originalFileContent = None
        with open(nodeDescProvider.path, "r") as f:
            originalFileContent = f.read()

        replaceFileContent = originalFileContent.replace('"not an integer"', '1')
        with open(nodeDescProvider.path, "w") as f:
            f.write(replaceFileContent)

        # Reload the node desc provider and assert it is valid
        nodeDescProvider.reload()
        assert nodeDescProvider.status == NodeDescProviderStatus.VALID

        # Attempt to register the node desc provider
        pluginManager.registerPluginProviders(plugin)
        assert pluginManager.isNodeDescRegistered(nodeDescProvider.name)

        # Reload the node again without any change
        nodeDescProvider.reload()
        assert pluginManager.isNodeDescRegistered(nodeDescProvider.name)

        # Hack to ensure that the timestamp of the file will be different after being rewritten
        # Without it, on some systems, the operation is too fast and the timestamp does not change,
        # cause the test to fail
        time.sleep(0.1)

        # Restore the node desc file to its original state (with a description error)
        with open(nodeDescProvider.path, "w") as f:
            f.write(originalFileContent)

        # Reload the node and assert it is invalid while still registered
        nodeDescProvider.reload()
        assert nodeDescProvider.status == NodeDescProviderStatus.DESC_ERROR
        assert pluginManager.isNodeDescRegistered(nodeDescProvider.name)

        # Remove the plugin
        pluginManager.removePlugin(plugin)

        # Re-add the plugin
        pluginManager.addPluginFromPath("pluginB", self.folder)
        nodeDescProvider = plugin.nodeDescProviders["PluginBNodeB"]
        assert nodeDescProvider.status == NodeDescProviderStatus.DESC_ERROR
        assert not pluginManager.isNodeDescRegistered(nodeDescProvider.name)

    def test_reloadNodeDescProviderSyntaxError(self):
        plugin = pluginManager.getPlugin("pluginB")
        assert plugin
        nodeDescProvider = plugin.nodeDescProviders["PluginBNodeA"]

        # Check that the node desc has been registered
        assert nodeDescProvider.status == NodeDescProviderStatus.VALID
        assert pluginManager.isNodeDescRegistered(nodeDescProvider.name)

        # Introduce a syntax error in the description
        originalFileContent = None
        with open(nodeDescProvider.path, "r") as f:
            originalFileContent = f.read()

        replaceFileContent = originalFileContent.replace('name="input",', 'name="input"')
        with open(nodeDescProvider.path, "w") as f:
            f.write(replaceFileContent)

        # Reload the node desc provider and assert it is invalid but still registered
        nodeDescProvider.reload()
        assert nodeDescProvider.status == NodeDescProviderStatus.DESC_ERROR
        assert pluginManager.isNodeDescRegistered(nodeDescProvider.name)

        # Restore the node desc file to its original state (with a description error)
        with open(nodeDescProvider.path, "w") as f:
            f.write(originalFileContent)

        # Assert the status is correct and the node is still registered
        nodeDescProvider.reload()
        assert nodeDescProvider.status == NodeDescProviderStatus.VALID
        assert pluginManager.isNodeDescRegistered(nodeDescProvider.name)


class TestVersionPlugins:
    def test_nodeVersionType(self):
        folder = os.path.join(pluginsFolder, "pluginA")
        with registeredPlugin("pluginA", folder):
            pluginA = pluginManager.getPlugin("pluginA")
            assert pluginA
            nodeA = pluginManager.getNodeDescProvider("PluginANodeA")
            assert nodeA
            assert nodeA.nodeDescClass().nodeVersionType == NodeVersionType.RELEASED

            nodeB = pluginManager.getNodeDescProvider("PluginANodeB")
            assert nodeB
            assert nodeB.nodeDescClass().nodeVersionType == NodeVersionType.BETA

            nodeInput = pluginManager.getNodeDescProvider("PluginAInitNode")
            assert nodeInput
            assert nodeInput.nodeDescClass().nodeVersionType == NodeVersionType.UNKNOWN

        with registeredPlugin("pluginA", folder, isUserPlugin=True):
            pluginA = pluginManager.getPlugin("pluginA")
            assert pluginA
            nodeA = pluginManager.getNodeDescProvider("PluginANodeA")
            assert nodeA
            assert nodeA.nodeDescClass().nodeVersionType == NodeVersionType.USER

            nodeB = pluginManager.getNodeDescProvider("PluginANodeB")
            assert nodeB
            assert nodeB.nodeDescClass().nodeVersionType == NodeVersionType.USER

            nodeInput = pluginManager.getNodeDescProvider("PluginAInitNode")
            assert nodeInput
            assert nodeInput.nodeDescClass().nodeVersionType == NodeVersionType.USER
