#!/usr/bin/env python
# coding:utf-8

import json
import logging
import sys

from meshroom.core.plugins.base import PluginType, NodeDescProviderStatus, SubmitterProviderStatus
from meshroom.core.plugins.loader import PLUGINS_ROOT_PACKAGE, PluginLoader
from .utils import writeFile


def _nodeDescSource(className: str) -> str:
    return (
        f"from meshroom.core import desc\n\n"
        f"class {className}(desc.Node):\n"
        f"    pass\n"
    )


def _submitterSource(className: str, name: str = None) -> str:
    name = name or className
    return (
        "from meshroom.core.submitter import BaseSubmitter\n\n"
        f"class {className}(BaseSubmitter):\n"
        f"    _name = \"{name}\"\n"
    )


def _brokenSource() -> str:
    return "raise RuntimeError('broken')\n"


class TestPluginLoader:

    def test_flatRoot(self, tmp_path):
        """ Standalone files directly in the plugin's root are discovered. """
        writeFile(tmp_path / "meshroom/MyNode.py", _nodeDescSource("MyNode"))

        loader = PluginLoader()
        plugin = loader.loadPlugin("flatRootPlugin", str(tmp_path), PluginType.PATH)

        assert plugin is not None
        assert list(plugin.nodeDescProviders.keys()) == ["MyNode"]
        assert plugin.nodeDescProviders["MyNode"].status == NodeDescProviderStatus.VALID

        loader.unloadPlugin("flatRootPlugin")

    def test_rootInitIgnored(self, tmp_path):
        """ The root's own "__init__.py" is ignored, even if it defines a node itself. """
        writeFile(tmp_path / "meshroom/__init__.py", _nodeDescSource("RootNode"))
        writeFile(tmp_path / "meshroom/MyNode.py", _nodeDescSource("MyNode"))

        loader = PluginLoader()
        plugin = loader.loadPlugin("rootInitIgnoredPlugin", str(tmp_path), PluginType.PATH)

        assert plugin is not None
        assert "RootNode" not in plugin.nodeDescProviders
        assert "MyNode" in plugin.nodeDescProviders

        loader.unloadPlugin("rootInitIgnoredPlugin")

    def test_packageSubfolder(self, tmp_path):
        """
        A subfolder with an "__init__.py" is loaded as a real package: "__init__.py" and every
        one of its direct children are scanned, whether or not "__init__.py" references them.
        """
        writeFile(tmp_path / "meshroom/pkgA/__init__.py", "from .impl import ExposedNode\n")
        writeFile(tmp_path / "meshroom/pkgA/impl.py", _nodeDescSource("ExposedNode"))
        writeFile(tmp_path / "meshroom/pkgA/other.py", _nodeDescSource("OtherNode"))

        loader = PluginLoader()
        plugin = loader.loadPlugin("packageSubfolderPlugin", str(tmp_path), PluginType.PATH)

        assert plugin is not None
        assert set(plugin.nodeDescProviders.keys()) == {"ExposedNode", "OtherNode"}

        loader.unloadPlugin("packageSubfolderPlugin")

    def test_nestedPackageTwoLevelsNotDiscovered(self, tmp_path):
        """ A package nested two levels from the root only has its "__init__.py" scanned. """
        writeFile(tmp_path / "meshroom/subpkgA/__init__.py")
        writeFile(tmp_path / "meshroom/subpkgA/subpkgB/__init__.py")
        writeFile(tmp_path / "meshroom/subpkgA/subpkgB/impl.py", _nodeDescSource("DeepNode"))

        loader = PluginLoader()
        plugin = loader.loadPlugin("nestedPackagePlugin", str(tmp_path), PluginType.PATH)

        # Nothing was found: subpkgB's own children are never reached.
        assert plugin is None

        loader.unloadPlugin("nestedPackagePlugin")

    def test_plainSubfolderOneLevel(self, tmp_path):
        """ A plain (non-package) subfolder only yields its own direct files, one level deep. """
        writeFile(tmp_path / "meshroom/plain/Shallow.py", _nodeDescSource("Shallow"))
        writeFile(tmp_path / "meshroom/plain/deeper/Deep.py", _nodeDescSource("Deep"))

        loader = PluginLoader()
        plugin = loader.loadPlugin("plainSubfolderPlugin", str(tmp_path), PluginType.PATH)

        assert plugin is not None
        assert list(plugin.nodeDescProviders.keys()) == ["Shallow"]

        loader.unloadPlugin("plainSubfolderPlugin")

    def test_nodeAndSubmitterTogether(self, tmp_path):
        """ Node descriptors and submitters are discovered together on the same plugin. """
        writeFile(tmp_path / "meshroom/MyNode.py", _nodeDescSource("MyNode"))
        writeFile(tmp_path / "meshroom/MySubmitter.py", _submitterSource("MySubmitter"))

        loader = PluginLoader()
        plugin = loader.loadPlugin("mixedPlugin", str(tmp_path), PluginType.PATH)

        assert plugin is not None
        assert list(plugin.nodeDescProviders.keys()) == ["MyNode"]
        assert list(plugin.submitterProviders.keys()) == ["MySubmitter"]
        assert plugin.submitterProviders["MySubmitter"].status == SubmitterProviderStatus.VALID

        loader.unloadPlugin("mixedPlugin")

    def test_brokenModuleDoesNotBlockOthers(self, tmp_path, caplog):
        """ A module that fails to import is logged as an issue, but its siblings still load. """
        writeFile(tmp_path / "meshroom/Broken.py", _brokenSource())
        writeFile(tmp_path / "meshroom/Good.py", _nodeDescSource("GoodNode"))

        loader = PluginLoader()
        with caplog.at_level(logging.WARNING):
            plugin = loader.loadPlugin("brokenPlugin", str(tmp_path), PluginType.PATH)

        assert plugin is not None
        assert list(plugin.nodeDescProviders.keys()) == ["GoodNode"]
        assert "Broken" in caplog.text

        loader.unloadPlugin("brokenPlugin")

    def test_emptyPluginReturnsNone(self, tmp_path):
        """ A plugin with no node, submitter, or template is not returned. """
        (tmp_path / "meshroom").mkdir()

        plugin = PluginLoader().loadPlugin("emptyPlugin", str(tmp_path), PluginType.PATH)

        assert plugin is None

    def test_missingMeshroomFolderReturnsNone(self, tmp_path):
        """ A plugin folder without a "meshroom" subfolder is not loaded. """
        plugin = PluginLoader().loadPlugin("noMeshroomFolderPlugin", str(tmp_path), PluginType.BUILTIN)

        assert plugin is None

    def test_hasMeshroomFolderFalse(self, tmp_path):
        """ With "hasMeshroomFolder=False", the plugin folder itself is the modules' root. """
        writeFile(tmp_path / "MyNode.py", _nodeDescSource("MyNode"))

        loader = PluginLoader()
        plugin = loader.loadPlugin(
            "flatFolderPlugin", str(tmp_path), PluginType.PATH, hasMeshroomFolder=False
        )

        assert plugin is not None
        assert list(plugin.nodeDescProviders.keys()) == ["MyNode"]

        loader.unloadPlugin("flatFolderPlugin")

    def test_duplicatePluginNameRejected(self, tmp_path):
        """ Loading a plugin under an already-loaded name is rejected. """
        pluginADir = tmp_path / "pluginA"
        pluginBDir = tmp_path / "pluginB"
        writeFile(pluginADir / "meshroom/MyNode.py", _nodeDescSource("MyNode"))
        writeFile(pluginBDir / "meshroom/MyNode.py", _nodeDescSource("MyNode"))

        loader = PluginLoader()
        first = loader.loadPlugin("duplicatePlugin", str(pluginADir), PluginType.PATH)
        second = loader.loadPlugin("duplicatePlugin", str(pluginADir), PluginType.PATH)
        third = loader.loadPlugin("duplicatePlugin", str(pluginBDir), PluginType.PATH)

        assert first is not None
        assert second is None
        assert third is None

        loader.unloadPlugin("duplicatePlugin")

    def test_unloadPluginAllowsReload(self, tmp_path):
        """ "unloadPlugin" releases a plugin's name so it can be loaded again. """
        writeFile(tmp_path / "meshroom/MyNode.py", _nodeDescSource("MyNode"))

        loader = PluginLoader()
        first = loader.loadPlugin("reloadablePlugin", str(tmp_path), PluginType.PATH)
        assert first is not None

        loader.unloadPlugin("reloadablePlugin")

        second = loader.loadPlugin("reloadablePlugin", str(tmp_path), PluginType.PATH)
        assert second is not None
        assert second is not first

        loader.unloadPlugin("reloadablePlugin")

    def test_isUserPlugin(self, tmp_path):
        """ "isUserPlugin" is propagated to the loaded Plugin object. """
        writeFile(tmp_path / "meshroom/MyNode.py", _nodeDescSource("MyNode"))

        loader = PluginLoader()
        plugin = loader.loadPlugin("userPlugin", str(tmp_path), PluginType.PATH, isUserPlugin=True)

        assert plugin is not None
        assert plugin.isUserPlugin is True

        loader.unloadPlugin("userPlugin")

    def test_templatesLoaded(self, tmp_path):
        """ Pipeline templates (".mgt" files) at the plugin's root are registered. """
        writeFile(tmp_path / "meshroom/MyNode.py", _nodeDescSource("MyNode"))
        writeFile(tmp_path / "meshroom/myTemplate.mgt", "{}")

        loader = PluginLoader()
        plugin = loader.loadPlugin("templatePlugin", str(tmp_path), PluginType.PATH)

        assert plugin is not None
        assert "myTemplate" in plugin.templates

        loader.unloadPlugin("templatePlugin")

    def test_uniqueNamespacePerPlugin(self, tmp_path):
        """ Two plugins shipping identically-named files never collide in sys.modules. """
        pluginADir = tmp_path / "pluginA"
        pluginBDir = tmp_path / "pluginB"
        writeFile(pluginADir / "meshroom/SharedName.py", _nodeDescSource("NodeFromA"))
        writeFile(pluginBDir / "meshroom/SharedName.py", _nodeDescSource("NodeFromB"))

        loader = PluginLoader()
        pluginA = loader.loadPlugin("namespacePluginA", str(pluginADir), PluginType.PATH)
        pluginB = loader.loadPlugin("namespacePluginB", str(pluginBDir), PluginType.PATH)

        assert pluginA is not None and pluginB is not None
        assert list(pluginA.nodeDescProviders.keys()) == ["NodeFromA"]
        assert list(pluginB.nodeDescProviders.keys()) == ["NodeFromB"]

        loader.unloadPlugin("namespacePluginA")
        loader.unloadPlugin("namespacePluginB")

    def test_virtualPackageModuleNames(self, tmp_path):
        """
        Every module a plugin provides is registered in sys.modules under the virtual
        "PLUGINS_ROOT_PACKAGE.<pluginName>" package, and its classes' "__module__" reflects
        that same dotted name, not the real file path it was loaded from.
        """
        writeFile(tmp_path / "meshroom/MyNodeA.py", _nodeDescSource("MyNodeA"))
        writeFile(tmp_path / "meshroom/pkg/__init__.py")
        writeFile(tmp_path / "meshroom/pkg/MyNodeB.py", _nodeDescSource("MyNodeB"))
        writeFile(tmp_path / "meshroom/folder/MyNodeC.py", _nodeDescSource("MyNodeC"))

        loader = PluginLoader()
        plugin = loader.loadPlugin("virtualPlugin", str(tmp_path), PluginType.PATH)

        assert plugin is not None

        rootModuleName = f"{PLUGINS_ROOT_PACKAGE}.virtualPlugin"
        flatModuleName = f"{rootModuleName}.MyNodeA"
        packageModuleName = f"{rootModuleName}.pkg"
        packageChildModuleName = f"{rootModuleName}.pkg.MyNodeB"
        folderChildModuleName = f"{rootModuleName}.folder.MyNodeC"

        # Every module is registered under the expected virtual dotted name.
        assert PLUGINS_ROOT_PACKAGE in sys.modules
        assert rootModuleName in sys.modules
        assert flatModuleName in sys.modules
        assert packageModuleName in sys.modules
        assert packageChildModuleName in sys.modules
        assert folderChildModuleName in sys.modules

        # Discovered classes report the virtual name, not their real file path.
        assert plugin.nodeDescProviders["MyNodeA"].nodeDescClass.__module__ == flatModuleName
        assert plugin.nodeDescProviders["MyNodeB"].nodeDescClass.__module__ == packageChildModuleName
        assert plugin.nodeDescProviders["MyNodeC"].nodeDescClass.__module__ == folderChildModuleName

        loader.unloadPlugin("virtualPlugin")

        # Unloading releases every module registered under the plugin's virtual package.
        # Leaves the shared root package itself (other plugins may still use it).
        assert rootModuleName not in sys.modules
        assert flatModuleName not in sys.modules
        assert packageModuleName not in sys.modules
        assert packageChildModuleName not in sys.modules
        assert folderChildModuleName not in sys.modules
        assert PLUGINS_ROOT_PACKAGE in sys.modules

    def test_configNameAndVersionOverride(self, tmp_path):
        """ "name"/"version" in the configuration file override the given plugin name/version. """
        writeFile(tmp_path / "meshroom/MyNode.py", _nodeDescSource("MyNode"))
        writeFile(tmp_path / "meshroom/config.json", json.dumps({
            "name": "overriddenName",
            "version": "1.2.3",
            "env": [{"key": "MY_VAR", "type": "string", "value": "myValue"}],
        }))

        loader = PluginLoader()
        plugin = loader.loadPlugin("originalName", str(tmp_path), PluginType.PATH, pluginVersion="0.0.1")

        assert plugin is not None
        assert plugin.name == "overriddenName"
        assert plugin.version == "1.2.3"
        assert plugin.configEnv["MY_VAR"] == "myValue"
        assert f"{PLUGINS_ROOT_PACKAGE}.overriddenName" in sys.modules

        loader.unloadPlugin("overriddenName")

    def test_configOverrideIgnoredForRezPlugin(self, tmp_path):
        """ For a Rez plugin, "name"/"version" from the configuration file are ignored: the
        Rez-resolved values take precedence. """
        writeFile(tmp_path / "meshroom/MyNode.py", _nodeDescSource("MyNode"))
        writeFile(tmp_path / "meshroom/config.json", json.dumps({
            "name": "shouldBeIgnored",
            "version": "9.9.9",
        }))

        loader = PluginLoader()
        plugin = loader.loadPlugin("rezPlugin", str(tmp_path), PluginType.REZ, pluginVersion="1.0.0")

        assert plugin is not None
        assert plugin.name == "rezPlugin"
        assert plugin.version == "1.0.0"

        loader.unloadPlugin("rezPlugin")

    def test_listConfigFormatWorks(self, tmp_path):
        """ A "config.json" using the flat-list format that only sets environment variables. """
        writeFile(tmp_path / "meshroom/MyNode.py", _nodeDescSource("MyNode"))
        writeFile(tmp_path / "meshroom/config.json", json.dumps(
            [{"key": "MY_VAR", "type": "string", "value": "myValue"}]
        ))

        loader = PluginLoader()
        plugin = loader.loadPlugin("listConfigPlugin", str(tmp_path), PluginType.PATH, pluginVersion="1.0.0")

        assert plugin is not None
        assert plugin.name == "listConfigPlugin"
        assert plugin.version == "1.0.0"
        assert plugin.configEnv["MY_VAR"] == "myValue"

        loader.unloadPlugin("listConfigPlugin")

    def test_invalidConfigNameAndVersionFallBack(self, tmp_path):
        """ An invalid "name"/"version" in the configuration file is ignored, falling back to the
        given values, with a warning logged. """
        writeFile(tmp_path / "meshroom/MyNode.py", _nodeDescSource("MyNode"))
        writeFile(tmp_path / "meshroom/config.json", json.dumps({
            "name": "invalid-name",
            "version": "not_a_version",
        }))

        loader = PluginLoader()
        plugin = loader.loadPlugin("fallbackPlugin", str(tmp_path), PluginType.PATH, pluginVersion="1.0.0")

        assert plugin is not None
        assert plugin.name == "fallbackPlugin"
        assert plugin.version == "1.0.0"

        loader.unloadPlugin("fallbackPlugin")
