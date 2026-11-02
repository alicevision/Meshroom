# coding:utf-8

from meshroom.core import pluginManager
from meshroom.core.desc.node import NodeVersionType
from meshroom.core.plugins.base import NodeDescProviderStatus
from meshroom.core.plugins.registry import PluginRegistry
from ..utils import registeredPlugin, writeFile

import json
import os
import shutil
import time

import pytest

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


class TestSearchPlugin:
    def test_availableRecordShadowedByInstalledPlugin(self, tmp_path):
        """
        An available PluginRecord sharing its name with an installed Plugin must not be
        returned when searching available plugins only, but the installed Plugin should
        still take precedence when both installed and available plugins are requested.
        """
        folder = os.path.join(pluginsFolder, "pluginA")
        with registeredPlugin("pluginA", folder):
            content = {"entries": [{"name": "pluginA", "url": "https://github.com/publisher/pluginA", "versions": ["1.0"]}]}
            path = writeFile(tmp_path / "registry.json", json.dumps(content))
            registry = PluginRegistry(path)
            registry.updateRecords()
            assert registry.getRecord("pluginA") is not None

            pluginManager._pluginRegistries[registry.name] = registry
            try:
                # Available-only: the record for "pluginA" is shadowed by the installed plugin.
                results = pluginManager.searchPlugin(["pluginA"], installed=False, available=True)
                assert all(result.name != "pluginA" for result in results)

                # Installed + available: the record for "pluginA" is shadowed by the installed plugin.
                results = pluginManager.searchPlugin(["pluginA"], installed=True, available=True)
                assert len(results) == 1
                assert results[0] is pluginManager.getPlugin("pluginA")
            finally:
                del pluginManager._pluginRegistries[registry.name]


class TestGetUpdateRecord:
    def _withRegistry(self, tmp_path, **entryOverrides):
        """ Register a temporary PluginRegistry with a single entry for "pluginA", merging overrides. """
        entry = {"name": "pluginA", "url": "https://github.com/publisher/pluginA", "versions": ["1.0"]}
        entry.update(entryOverrides)
        path = writeFile(tmp_path / "registry.json", json.dumps({"entries": [entry]}))
        registry = PluginRegistry(path)
        registry.updateRecords()
        assert registry.getRecord("pluginA") is not None
        pluginManager._pluginRegistries[registry.name] = registry
        return registry

    def test_updateAvailableWhenVersionDiffers(self, tmp_path):
        """ A record sharing the plugin's name/publisher but a different version is an available update. """
        folder = os.path.join(pluginsFolder, "pluginA")
        with registeredPlugin("pluginA", folder):
            plugin = pluginManager.getPlugin("pluginA")
            registry = self._withRegistry(tmp_path, publisher=plugin.publisher, versions=["2.0"])
            try:
                record = pluginManager.getUpdateRecord(plugin)
                assert record is not None
                assert record.version == "2.0"
            finally:
                del pluginManager._pluginRegistries[registry.name]

    def test_noUpdateWhenVersionMatches(self, tmp_path):
        """ A record with the same name/publisher and the same version is not an available update. """
        folder = os.path.join(pluginsFolder, "pluginA")
        with registeredPlugin("pluginA", folder):
            plugin = pluginManager.getPlugin("pluginA")
            registry = self._withRegistry(tmp_path, publisher=plugin.publisher, versions=[plugin.version])
            try:
                assert pluginManager.getUpdateRecord(plugin) is None
            finally:
                del pluginManager._pluginRegistries[registry.name]

    def _installedPlugin(self, tmp_path, version, sourceVersion=None):
        """ Return the folder of a copy of "pluginA" at "version", installed from "sourceVersion" of its source. """
        folder = tmp_path / "pluginA"
        shutil.copytree(os.path.join(pluginsFolder, "pluginA"), folder, ignore=shutil.ignore_patterns("__pycache__"))
        lock = {"name": "pluginA", "version": version, "publisher": "publisher"}
        if sourceVersion:
            lock["source"] = {"url": "https://github.com/publisher/pluginA", "version": sourceVersion}
        writeFile(folder / "plugin.lock", json.dumps(lock))
        return str(folder)

    @pytest.mark.parametrize("version,sourceVersion,recordVersion,expected", [
        # The tag of a release, without its "v" in the plugin's own version.
        ("1.0.3", "v1.0.3", "v1.0.3", None),
        # A commit of a branch, which the plugin's own version does not mention.
        ("1.0.3", "main+02d976e", "main+02d976e", None),
        ("1.0.3", "main+02d976e", "main+1475613", "main+1475613"),
        # An older tag, even if it did not bump the plugin's own version.
        ("1.0.3", "v1.0.2", "v1.0.3", "v1.0.3"),
        # Installed before the source was recorded: only the "v" of a tag can be told apart.
        ("1.0.3", None, "v1.0.3", None),
        ("1.0.2", None, "v1.0.3", "v1.0.3"),
    ])
    def test_comparesTheVersionInstalledFromTheSource(self, tmp_path, version, sourceVersion, recordVersion, expected):
        """ A record is compared to the version of the source the plugin was installed from, if known. """
        with registeredPlugin("pluginA", self._installedPlugin(tmp_path, version, sourceVersion)):
            plugin = pluginManager.getPlugin("pluginA")
            registry = self._withRegistry(tmp_path, publisher="publisher", versions=[recordVersion])
            try:
                record = pluginManager.getUpdateRecord(plugin)
                assert (record.version if record else None) == expected
            finally:
                del pluginManager._pluginRegistries[registry.name]

    def test_noUpdateWhenPublisherDiffers(self, tmp_path):
        """ A record with a different publisher is not considered an available update. """
        folder = os.path.join(pluginsFolder, "pluginA")
        with registeredPlugin("pluginA", folder):
            plugin = pluginManager.getPlugin("pluginA")
            registry = self._withRegistry(tmp_path, publisher=f"not-{plugin.publisher}", versions=["2.0"])
            try:
                assert pluginManager.getUpdateRecord(plugin) is None
            finally:
                del pluginManager._pluginRegistries[registry.name]


class TestRenamedPlugin:
    """ A plugin renamed by its source is found from the url it was installed from. """

    def _installedPlugin(self, tmp_path, sourceUrl):
        """ Return the folder of a copy of "pluginA" named "oldName", installed from "sourceUrl". """
        folder = tmp_path / "oldName"
        shutil.copytree(os.path.join(pluginsFolder, "pluginA"), folder, ignore=shutil.ignore_patterns("__pycache__"))
        lock = {"name": "oldName", "version": "1.0", "publisher": "publisher",
                "source": {"url": sourceUrl, "version": "1.0"}}
        writeFile(folder / "plugin.lock", json.dumps(lock))
        return str(folder)

    def _withRegistry(self, tmp_path):
        """ Register a temporary PluginRegistry describing the plugin under the name "newName". """
        entry = {"name": "newName", "url": "https://github.com/publisher/newName", "versions": ["2.0"]}
        path = writeFile(tmp_path / "registry.json", json.dumps({"entries": [entry]}))
        registry = PluginRegistry(path)
        registry.updateRecords()
        pluginManager._pluginRegistries[registry.name] = registry
        return registry

    def test_updateRecord(self, tmp_path):
        """ The record with the url the plugin was installed from is an update of the plugin, not another plugin. """
        with registeredPlugin("oldName", self._installedPlugin(tmp_path, "https://github.com/publisher/newName.git/")):
            plugin = pluginManager.getPlugin("oldName")
            assert plugin.sourceUrl == "https://github.com/publisher/newName.git/"
            registry = self._withRegistry(tmp_path)
            try:
                record = pluginManager.getUpdateRecord(plugin)
                assert record is not None
                assert record.name == "newName"
                assert pluginManager.searchPlugin(["newName"], installed=False, available=True) == []
            finally:
                del pluginManager._pluginRegistries[registry.name]

    def test_otherSource(self, tmp_path):
        """ A record with another url is another plugin. """
        with registeredPlugin("oldName", self._installedPlugin(tmp_path, "https://github.com/publisher/oldName")):
            plugin = pluginManager.getPlugin("oldName")
            registry = self._withRegistry(tmp_path)
            try:
                assert pluginManager.getUpdateRecord(plugin) is None
                assert [record.name for record in pluginManager.searchPlugin(["newName"], installed=False)] == ["newName"]
            finally:
                del pluginManager._pluginRegistries[registry.name]
