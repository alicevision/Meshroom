from __future__ import annotations

import importlib
import importlib.machinery
import importlib.util
import logging
import os
import sys
import traceback

from types import ModuleType
from pathlib import Path

from meshroom.core import desc
from meshroom.core.submitter import BaseSubmitter
from meshroom.core.plugins.base import Plugin, PluginType, NodeDescProvider

# The virtual package all the imported plugins are nested in.
# Registered directly in sys.modules.
PLUGINS_ROOT_PACKAGE = "_meshroomPlugins"


class _LoadIssues:
    """
    Collects the issues found while loading a single plugin.
    """

    def __init__(self):
        self.loading: list[str] = []
        self.nodeDescProviders: list[str] = []
        self.submitterProviders: list[str] = []

    def log(self, pluginName: str):
        """ Log one consolidated message per issue type found while loading the plugin "pluginName". """
        if self.loading:
            logging.warning(self._format(pluginName, self.loading))
        if self.nodeDescProviders:
            logging.error(self._format(pluginName, self.nodeDescProviders))
        if self.submitterProviders:
            logging.error(self._format(pluginName, self.submitterProviders))

    @staticmethod
    def _format(pluginName: str, messages: list[str]) -> str:
        """ Format "messages" into a single, bulleted message for the plugin "pluginName". """
        return f"Plugin '{pluginName}':" + "".join(f"\n  - {message}" for message in messages)


class PluginLoader:
    """
    Loads/Unloads a plugin into a private virtual package.

    Every plugin is loaded under its own dotted name "PLUGINS_ROOT_PACKAGE.<pluginName>",
    registered directly in sys.modules.
    """

    def loadPlugin(self,
                    pluginName: str,
                    pluginFolder: str,
                    pluginType: PluginType,
                    isUserPlugin: bool = False,
                    hasMeshroomFolder: bool = True) -> Plugin:
        """
        Load the plugin located in "pluginFolder" and return it.

        Python modules are expected in a "meshroom" folder, unless the plugin folder is itself the
        folder. Every standalone Python file at its root, every direct subfolder that is a real
        Python package, and every standalone Python file directly inside a plain (non-package)
        subfolder is loaded. A NodeDescProvider is created for each node description that is found.
        A SubmitterProvider for each submitter class, that is found. The templates and the configuration 
        file are read from "pluginFolder".

        Args:
            pluginName: the name of the plugin.
            pluginFolder: the plugin's root folder.
            pluginType: the type of the plugin.
            isUserPlugin: whether the plugin is a user plugin (not maintained by the core Meshroom team).
            hasMeshroomFolder: whether "pluginFolder" directly contains the plugin's modules, instead of
                        gathering them in a "meshroom" folder.

        Returns:
            Plugin: the loaded plugin, or None if its folders do not exist, if its name is already
                    used, or if it does not provide any node description, submitter, or template.
        """
        if not os.path.isdir(pluginFolder):
            logging.info(f"Plugin folder '{pluginFolder}' does not exist.")
            return None

        # Case where the folder directly contains the plugin's modules, while the other plugins are
        # expected to gather modules in a "meshroom" folder.
        mrFolder = Path(pluginFolder)

        if hasMeshroomFolder:
            mrFolder = Path(pluginFolder, "meshroom")
            if not mrFolder.is_dir():
                logging.info(f"Plugin folder '{pluginFolder}' does not contain a 'meshroom' folder.")
                return None

        # The plugin's name prefixes its modules.
        # Two plugins shipping identically named files do not collide in sys.modules.
        pluginPackage = f"{PLUGINS_ROOT_PACKAGE}.{pluginName}"

        # Reject a plugin whose name is already used.
        if pluginPackage in sys.modules:
            logging.warning(f"A plugin '{pluginName}' has already been loaded.")
            return None

        # Initialize the plugin object.
        plugin = Plugin(pluginName, mrFolder)
        plugin.isUserPlugin = isUserPlugin

        # Recursive load of modules.
        issues = _LoadIssues()
        self._loadRootFolder(plugin, pluginPackage, mrFolder, issues)

        # Log issues.
        issues.log(pluginName)

        # Check if the plugin is empty.
        if (len(plugin.nodeDescProviders) <= 0 
                and len(plugin.submitterProviders) <= 0
                and len(plugin.templates) <= 0):
            return None

        return plugin

    def unloadPlugin(self, pluginName: str):
        """
        Remove from sys.modules the virtual package of the plugin named "pluginName", as well as
        every module that has been loaded under it, so that the plugin can be loaded again.

        Args:
            pluginName: the name of the plugin to unload.
        """
        pluginPackage = f"{PLUGINS_ROOT_PACKAGE}.{pluginName}"
        for moduleName in [name for name in sys.modules if name == pluginPackage or name.startswith(f"{pluginPackage}.")]:
            del sys.modules[moduleName]

    def _loadRootFolder(self, plugin: Plugin, packageName: str, folderRootPath: Path, issues: _LoadIssues):
        """
        Load plugin's root folder. The root itself is always treated as a flat folder,
        even if it contains an "__init__.py" (which is ignored). Each direct subfolder
        is loaded as a package folder if it contains an "init.py", or as a flat folder otherwise.

        Args:
            plugin: the Plugin object to attach discovered node/submitter providers to.
            packageName: the dotted name of the virtual package the folder stands for.
            folderRootPath: the plugin's root folder to load.
            issues: the collector for the issues found while loading the plugin.
        """
        self._loadFlatFolder(plugin, packageName, folderRootPath, issues)

        for subFolderPath in sorted(p for p in folderRootPath.iterdir()
                                     if p.is_dir() and not p.name.startswith(("__", "."))):
            self._loadFolder(plugin, f"{packageName}.{subFolderPath.name}", subFolderPath, issues)

    def _loadFolder(self, plugin: Plugin, packageName: str, folderPath: Path, issues: _LoadIssues):
        """
        Load "folderPath" as a package if it contains an "__init__.py", or as a flat,
        file-by-file folder otherwise.

        Args:
            plugin: the Plugin object to attach discovered node/submitter providers to.
            packageName: the dotted name of the virtual package the folder stands for.
            folderPath: the folder to load.
            issues: the collector for the issues found while loading the plugin.
        """
        if (folderPath / "__init__.py").is_file():
            self._loadPackageFolder(plugin, packageName, folderPath, issues)
        else:
            self._loadFlatFolder(plugin, packageName, folderPath, issues)

    def _loadPackageFolder(self, plugin: Plugin, packageName: str, folderPath: Path, issues: _LoadIssues):
        """
        Load "folderPath" as a real Python package, executing its "__init__.py" instead of
        faking one, so relative imports and package-level wiring between its modules behave
        exactly as they would for a normally installed package. Every direct child of the
        package, every standalone Python file, and every subfolder that is itself a package,
        is then individually loaded and scanned, one level deep.

        Args:
            plugin: the Plugin object to attach discovered node/submitter providers to.
            packageName: the dotted name to load the package under.
            folderPath: the package's folder, containing an "__init__.py".
            issues: the collector for the issues found while loading the plugin.
        """
        # Register package for sub-folders.
        parentName = packageName.rpartition(".")[0]
        if parentName:
            self._registerPackage(parentName)

        # Load init module.
        initModule = sys.modules.get(packageName) or self._execModule(
            packageName, folderPath / "__init__.py", issues, submoduleSearchLocations=[str(folderPath)])
        if initModule is None:
            return

        self._collectProviders(plugin, initModule, issues)

        # Every direct child is scanned too, regardless of whether "__init__.py" imports it.
        for entryPath in sorted(folderPath.iterdir()):
            if entryPath.name.startswith(("__", ".")):
                continue

            if entryPath.is_dir():
                if not (entryPath / "__init__.py").is_file():
                    # Not itself a package: not walked, matching the one-level rule for plain
                    # subfolders elsewhere in this loader.
                    continue
                childName = f"{packageName}.{entryPath.name}"
                childModule = sys.modules.get(childName) or self._execModule(
                    childName, entryPath / "__init__.py", issues, submoduleSearchLocations=[str(entryPath)])
            elif entryPath.suffix == ".py":
                childName = f"{packageName}.{entryPath.stem}"
                childModule = sys.modules.get(childName) or self._execModule(childName, entryPath, issues)
            else:
                continue

            if childModule is None:
                continue
            self._collectProviders(plugin, childModule, issues)

    def _loadFlatFolder(self, plugin: Plugin, packageName: str, folderPath: Path, issues: _LoadIssues):
        """
        Load every Python file directly contained in "folderPath" as a module of the virtual
        package "packageName", and collect the node/submitter providers these modules define.

        Args:
            packageName: the dotted name of the virtual package the folder stands for.
            folderPath: the folder containing the Python files to load.
            issues: the collector for the issues found while loading the plugin.
        """
        for filePath in sorted(folderPath.glob("*.py")):
            # Skip special/dunder files like __init__.py
            if filePath.stem.startswith("__"):
                continue

            module = self._execModule(f"{packageName}.{filePath.stem}", filePath, issues)
            if not module:
                continue

            # Register the package now that the folder is known to provide modules.
            self._registerPackage(packageName, folderPath)
            self._collectProviders(plugin, module, issues)

    def _execModule(self, moduleName: str, filePath: Path, issues: _LoadIssues,
                     submoduleSearchLocations: list[str] = None) -> ModuleType:
        """
        Load the Python file "filePath" as the module "moduleName" and register it in sys.modules.

        Nothing is left registered when the loading fails, so that a returned module and an entry in
        sys.modules always come together.

        Args:
            moduleName: the unique dotted name to load the module under.
            filePath: the path of the Python file to load.
            issues: the collector for the issues found while loading the plugin.
            submoduleSearchLocations: if provided, "filePath" is treated as the "__init__.py" of a
                                     real package whose submodules are looked up in these folders.

        Returns:
            ModuleType: the loaded module, or None if it could not be loaded.
        """
        spec = importlib.util.spec_from_file_location(moduleName, filePath,
                                                      submodule_search_locations=submoduleSearchLocations)
        if spec is None or spec.loader is None:
            issues.loading.append(f'Could not create the module spec for "{filePath}".')
            return None

        module = importlib.util.module_from_spec(spec)
        sys.modules[moduleName] = module

        try:
            spec.loader.exec_module(module)
        except Exception as exc:
            # The module has been left partially initialized: unregister it, otherwise any
            # subsequent import of that name would silently return the broken module.
            sys.modules.pop(moduleName, None)
            issues.loading.append(f'Failed to load the module "{moduleName}" from "{filePath}"'
                                   f'{self._formatExceptionMessage(exc)}')
            return None

        return module

    def _collectProviders(self, plugin: Plugin, module: ModuleType, issues: _LoadIssues):
        """
        Add to the plugin a node provider for every node description, and a submitter provider for
        every submitter class, that "module" defines.

        Args:
            module: the module to scan for node description classes and submitter classes.
            issues: the collector for the issues found while loading the plugin.
        """
        for attrName in dir(module):
            attr = getattr(module, attrName)
            if not isinstance(attr, type) or attr.__module__ != module.__name__:
                continue

            if issubclass(attr, desc.BaseNode):
                try:
                    plugin.addNodeDescProvider(NodeDescProvider(attr, plugin))
                except Exception as exc:
                    issues.nodeDescProviders.append(f'Failed to create the node provider for "{attrName}" from '
                                f'"{module.__file__}"{self._formatExceptionMessage(exc)}')
            elif issubclass(attr, BaseSubmitter):
                try:
                    plugin.addSubmitterProvider(attr)
                except Exception as exc:
                    issues.submitterProviders.append(f'Failed to create the submitter provider for "{attrName}" from '
                                f'"{module.__file__}"{self._formatExceptionMessage(exc)}')

    def _registerPackage(self, packageName: str, packagePath: Path = None):
        """
        Register "packageName" in sys.modules as a virtual package, together with every parent
        package it is nested in that is not registered yet, up to PLUGINS_ROOT_PACKAGE.

        Args:
            packageName: the dotted name of the virtual package to register.
            packagePath: the folder the package's modules are loaded from. It must be provided for
                        the packages directly containing modules that can be reloaded.
        """
        if packageName in sys.modules:
            return

        # A module is resolved through its parent package, so the whole chain has to be registered.
        parentName = packageName.rpartition(".")[0]
        if parentName:
            self._registerPackage(parentName)

        # A spec without a loader but with search locations describes a package.
        spec = importlib.machinery.ModuleSpec(packageName, None, is_package=True)
        if packagePath:
            spec.submodule_search_locations.append(str(packagePath))

        sys.modules[packageName] = importlib.util.module_from_spec(spec)

    def _formatExceptionMessage(self, exc: Exception) -> str:
        """
        Format an exception raised while loading a plugin into a message detailing where it comes from.
        The location of the last call, the line of code that raised it and the full traceback are all
        reported, as plugin authors need them to debug their nodes.

        Args:
            exc: the exception to format.

        Returns:
            str: the formatted error message, to be appended to a description of what failed.
        """
        # Not using traceback.format_exception(exc): its single-argument form requires Python 3.10.
        fullTraceback = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        tb = traceback.extract_tb(exc.__traceback__)
        if not tb:
            return f" ({type(exc).__name__}): {exc}\n{fullTraceback}"

        lastCall = tb[-1]
        return (f" ({type(exc).__name__}): {exc}\n"
                # filename:lineNumber functionName
                f"{lastCall.filename}:{lastCall.lineno} {lastCall.name}\n"
                # line of code with the error
                f"{lastCall.line}\n"
                # Full traceback
                f"{fullTraceback}")