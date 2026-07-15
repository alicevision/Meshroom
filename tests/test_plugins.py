# coding:utf-8

from meshroom.core import pluginManager
from meshroom.core.desc.node import NodeVersionType
from meshroom.core.plugins.base import NodeDescProviderStatus
from .utils import overrideOsEnvironmentVariables, registeredPlugin

from pathlib import Path
import os
import time


class TestPluginWithValidNodesOnly:

    @classmethod
    def setup_class(cls):
        cls.folder = os.path.join(os.path.dirname(__file__), "plugins", "pluginA")
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
        assert str(plugin.path) == os.path.join(os.path.dirname(__file__), "plugins", "pluginA", "meshroom")

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
        assert plugin.templates[name] == os.path.join(str(plugin.path), "sharedTemplate.mg")

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
        cls.folder = os.path.join(os.path.dirname(__file__), "plugins", "pluginB")
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
        assert str(plugin.path) == os.path.join(os.path.dirname(__file__), "plugins", "pluginB", "meshroom")

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


class TestPluginsConfiguration:
    CONFIG_PATH = ("CONFIG_PATH", "sharedTemplate.mg", "config.json")
    ERRONEOUS_CONFIG_PATH = ("ERRONEOUS_CONFIG_PATH", "erroneous_path", "not_erroneous_path")
    CONFIG_STRING = ("CONFIG_STRING", "configFile", "notConfigFile")

    CONFIG_KEYS = [CONFIG_PATH[0], ERRONEOUS_CONFIG_PATH[0], CONFIG_STRING[0]]

    def test_loadedConfig(self):
        # Check that the config.json file for the plugins in the "plugins" directory is
        # correctly loaded
        folder = os.path.join(os.path.dirname(__file__), "plugins", "pluginA")
        with registeredPlugin("pluginA", folder):
            plugin = pluginManager.getPlugin("pluginA")
            assert plugin

            # Check that the config file has been properly loaded
            config = plugin.configEnv
            configFullEnv = plugin.configFullEnv
            assert len(config) == 3, "The configuration file contains exactly 3 keys."
            assert len(configFullEnv) >= len(os.environ) and \
                len(configFullEnv) == len(os.environ) + len(config), \
                "The configuration environment should have the same number of keys as " \
                "os.environ and the configuration file"

            # Check that all the keys have been properly read
            assert list(config.keys()) == self.CONFIG_KEYS

            # Check that the valid path has been correctly read, resolved and set
            assert configFullEnv[self.CONFIG_PATH[0]] == config[self.CONFIG_PATH[0]]
            assert configFullEnv[self.CONFIG_PATH[0]] == Path(
                os.path.join(plugin.path, self.CONFIG_PATH[1])).resolve().as_posix()

            # Check that the invalid path has been read, unresolved, and set
            assert configFullEnv[self.ERRONEOUS_CONFIG_PATH[0]] == self.ERRONEOUS_CONFIG_PATH[1]
            assert config[self.ERRONEOUS_CONFIG_PATH[0]] == self.ERRONEOUS_CONFIG_PATH[1]

            # Check that the string has been correctly read and set
            assert configFullEnv[self.CONFIG_STRING[0]] == self.CONFIG_STRING[1]
            assert config[self.CONFIG_STRING[0]] == self.CONFIG_STRING[1]

    def test_loadedConfigWithOnlyExistingKeys(self):
        # Set the keys from the config file in the current environment
        environment = {
            self.CONFIG_PATH[0]: self.CONFIG_PATH[2],
            self.ERRONEOUS_CONFIG_PATH[0]: self.ERRONEOUS_CONFIG_PATH[2],
            self.CONFIG_STRING[0]: self.CONFIG_STRING[2]
        }
        folder = os.path.join(os.path.dirname(__file__), "plugins", "pluginA")
        with (overrideOsEnvironmentVariables(environment), registeredPlugin("pluginA", folder)):
            plugin = pluginManager.getPlugin("pluginA")
            assert plugin

            # Check that the config file has been properly loaded and read
            # Environment variables that are already set should not have any effect on that
            # reading of values
            config = plugin.configEnv
            assert len(config) == 3
            assert list(config.keys()) == self.CONFIG_KEYS
            assert config[self.CONFIG_PATH[0]] == Path(
                os.path.join(plugin.path, self.CONFIG_PATH[1])).resolve().as_posix()
            assert config[self.ERRONEOUS_CONFIG_PATH[0]] == self.ERRONEOUS_CONFIG_PATH[1]
            assert config[self.CONFIG_STRING[0]] == self.CONFIG_STRING[1]

            # Check that the values of the configuration file are not taking precedence over
            # those in the environment
            configFullEnv = plugin.configFullEnv
            assert all(key in configFullEnv for key in config.keys())

            assert config[self.CONFIG_PATH[0]] != self.CONFIG_PATH[2]
            assert configFullEnv[self.CONFIG_PATH[0]] == self.CONFIG_PATH[2]

            assert config[self.ERRONEOUS_CONFIG_PATH[0]] != self.ERRONEOUS_CONFIG_PATH[2]
            assert configFullEnv[self.ERRONEOUS_CONFIG_PATH[0]] == self.ERRONEOUS_CONFIG_PATH[2]

            assert config[self.CONFIG_STRING[0]] != self.CONFIG_STRING[2]
            assert configFullEnv[self.CONFIG_STRING[0]] == self.CONFIG_STRING[2]

    def test_loadedConfigWithSomeExistingKeys(self):
        # Set some keys from the config file in the current environment
        environment = {
            self.ERRONEOUS_CONFIG_PATH[0]: self.ERRONEOUS_CONFIG_PATH[2],
            self.CONFIG_STRING[0]: self.CONFIG_STRING[2]
        }

        folder = os.path.join(os.path.dirname(__file__), "plugins", "pluginA")
        with (overrideOsEnvironmentVariables(environment), registeredPlugin("pluginA", folder)):
            plugin = pluginManager.getPlugin("pluginA")
            assert plugin

            # Check that the config file has been properly loaded and read
            # Environment variables that are already set should not have any effect on that
            # reading of values
            config = plugin.configEnv
            assert len(config) == 3
            assert list(config.keys()) == self.CONFIG_KEYS
            assert config[self.CONFIG_PATH[0]] == Path(
                os.path.join(plugin.path, self.CONFIG_PATH[1])).resolve().as_posix()
            assert config[self.ERRONEOUS_CONFIG_PATH[0]] == self.ERRONEOUS_CONFIG_PATH[1]
            assert config[self.CONFIG_STRING[0]] == self.CONFIG_STRING[1]

            # Check that the values of the configuration file are not taking precedence over
            # those in the environment
            configFullEnv = plugin.configFullEnv
            assert all(key in configFullEnv for key in config.keys())

            assert config[self.CONFIG_PATH[0]] == Path(os.path.join(
                plugin.path, self.CONFIG_PATH[1])).resolve().as_posix()
            assert configFullEnv[self.CONFIG_PATH[0]] == Path(os.path.join(
                plugin.path, self.CONFIG_PATH[1])).resolve().as_posix()

            assert config[self.ERRONEOUS_CONFIG_PATH[0]] != self.ERRONEOUS_CONFIG_PATH[2]
            assert configFullEnv[self.ERRONEOUS_CONFIG_PATH[0]] == self.ERRONEOUS_CONFIG_PATH[2]

            assert config[self.CONFIG_STRING[0]] != self.CONFIG_STRING[2]
            assert configFullEnv[self.CONFIG_STRING[0]] == self.CONFIG_STRING[2]


class TestVersionPlugins:
    def test_nodeVersionType(self):
        folder = os.path.join(os.path.dirname(__file__), "plugins", "pluginA")
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
