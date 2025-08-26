# coding:utf-8

from meshroom.core import pluginManager, loadClassesNodes
from meshroom.core.plugins import NodePluginStatus, Plugin
from .utils import registeredPlugins

from pathlib import Path
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


class TestPluginsConfiguration:
    CONFIG_PATH = ("CONFIG_PATH", "sharedTemplate.mg", "config.json")
    ERRONEOUS_CONFIG_PATH = ("ERRONEOUS_CONFIG_PATH", "erroneous_path", "not_erroneous_path")
    CONFIG_STRING = ("CONFIG_STRING", "configFile", "notConfigFile")

    CONFIG_KEYS = [CONFIG_PATH[0], ERRONEOUS_CONFIG_PATH[0], CONFIG_STRING[0]]

    def test_loadedConfig(self):
        # Check that the config.json file for the plugins in the "plugins" directory is
        # correctly loaded
        folder = os.path.join(os.path.dirname(__file__), "plugins")
        with registeredPlugins(folder):
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
        env = os.environ.copy()
        os.environ[self.CONFIG_PATH[0]] = self.CONFIG_PATH[2]
        os.environ[self.ERRONEOUS_CONFIG_PATH[0]] = self.ERRONEOUS_CONFIG_PATH[2]
        os.environ[self.CONFIG_STRING[0]] = self.CONFIG_STRING[2]

        folder = os.path.join(os.path.dirname(__file__), "plugins")
        with registeredPlugins(folder):
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

        # Restore os.environ to its original state
        os.environ = env

    def test_loadedConfigWithSomeExistingKeys(self):
        # Set some keys from the config file in the current environment
        env = os.environ.copy()
        os.environ[self.ERRONEOUS_CONFIG_PATH[0]] = self.ERRONEOUS_CONFIG_PATH[2]
        os.environ[self.CONFIG_STRING[0]] = self.CONFIG_STRING[2]

        folder = os.path.join(os.path.dirname(__file__), "plugins")
        with registeredPlugins(folder):
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

        # Restore os.environ to its original state
        os.environ = env
