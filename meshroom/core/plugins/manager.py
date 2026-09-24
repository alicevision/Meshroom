from __future__ import annotations

import logging
import time

from typing import Optional
from pathlib import Path

from meshroom.common import BaseObject, Property, Slot
from meshroom.env import EnvVar
from meshroom.core.plugins.loader import PluginLoader
from meshroom.core.plugins.registry import PluginRegistry
from meshroom.core.plugins.record import PluginRecord
from meshroom.core.plugins.base import (
    Plugin, PluginType, NodeDescProvider, NodeDescProviderStatus,
    SubmitterProvider, SubmitterProviderStatus,
)


class PluginManager(BaseObject):
    """
    Manager for all the loaded Plugin objects as well as the registered NodeDescProvider objects and
    SubmitterProvider objects.

    Members:
        pluginLoader: handle plugin loading in a common virtual package
        plugins: dictionary containing all the loaded Plugins, with their name as the key
        nodeDescProviders: dictionary containing all the NodeDescProviders that have been registered,
                            with their name as the key
        submitterProviders: dictionary containing all the SubmitterProviders that have been registered,
                            with the name of the submitter as the key
    """

    def __init__(self, parent: BaseObject = None):
        super().__init__(parent)
        self._pluginLoader: PluginLoader = PluginLoader()  # plugin loader in virtual package
        self._pluginRegistries: dict[str, PluginRegistry] = {}  # plugin registries
        self._plugins: dict[str, Plugin] = {}  # loaded plugins
        self._nodeDescProviders: dict[str, NodeDescProvider] = {}  # registered node descriptor providers
        self._submitterProviders: dict[str, SubmitterProvider] = {}  # registered submitter providers

    # Whether local plugin management is enabled ("MESHROOM_LOCAL_PLUGINS").
    localPluginsEnabled = Property(bool, lambda self: EnvVar.get(EnvVar.MESHROOM_LOCAL_PLUGINS), constant=True)

    def _addPlugin(self,
                   pluginName: str,
                   pluginFolder: str,
                   pluginType: PluginType,
                   pluginVersion: Optional[str] = None,
                   isUserPlugin: bool = False,
                   hasMeshroomFolder: bool = True,
                   registerProviders: bool = True):
        """
        Add a Plugin object and register the valid node description and submitter providers it contains.

        A node description or submitter provider is not registered if it is invalid, or if its name is
        already registered under another plugin: in that case, it remains part of "plugin" but is not
        made available through the manager.

        Args:
            pluginName: the name of the plugin.
            pluginFolder: the plugin's root folder.
            pluginType: the type of the plugin.
            pluginVersion: the version of the plugin.
            isUserPlugin: whether the plugin is a user plugin (not maintained by the core Meshroom team).
            hasMeshroomFolder: whether "pluginFolder" directly contains the plugin's modules, instead of
                        gathering them in a "meshroom" folder.
            registerProviders: True if all the valid providers from the plugin should be registered.
        """
        startTime = time.perf_counter()
        plugin = self._pluginLoader.loadPlugin(pluginName=pluginName,
                                               pluginFolder=pluginFolder,
                                               pluginType=pluginType,
                                               pluginVersion=pluginVersion,
                                               isUserPlugin=isUserPlugin,
                                               hasMeshroomFolder=hasMeshroomFolder,
                                               parent=self)
        if plugin:
            if self.getPlugin(plugin.name):
                logging.warning(f"Plugin {plugin.name} is already registered.")
                return
            self._plugins[plugin.name] = plugin

            if registerProviders:
                self.registerPluginProviders(plugin)
            logging.debug(f"Plugin '{pluginName}' loaded in {time.perf_counter() - startTime:.3f}s")

    def addPluginFromRez(self, rezPackageName: str, rezPackageVersion: str, rezPackageFolder: str,
                         isUserPlugin: bool = False, registerProviders: bool = True):
        """
        Load a plugin resolved through Rez and register its valid providers.

        The plugin's modules are expected in a "meshroom" folder inside "rezPackageFolder", and its
        process environment is built by resolving a Rez environment for its subrequires.

        Args:
            rezPackageName: the name of the Rez package, used as the plugin's name.
            rezPackageVersion: the version of the Rez package, used as the plugin's version.
            rezPackageFolder: the resolved root folder of the Rez package.
            isUserPlugin: whether the plugin is a user plugin (not maintained by the core Meshroom team).
            registerProviders: True if all the valid providers from the plugin should be registered.
        """
        self._addPlugin(rezPackageName, rezPackageFolder, PluginType.REZ, pluginVersion=rezPackageVersion,
                        isUserPlugin=isUserPlugin, hasMeshroomFolder=True, registerProviders=registerProviders)

    def addPluginFromPath(self, defaultPluginName: str, pluginFolder: str, pluginVersion: Optional[str] = None,
                          isUserPlugin: bool = False, registerProviders: bool = True):
        """
        Load a plugin located at an arbitrary path and register its valid providers.

        The plugin's modules are expected in a "meshroom" folder inside "pluginFolder", and its
        process environment is built from that folder's directory tree ("bin"/"lib"/"lib64"/"venv").

        Args:
            defaultPluginName: the name to register the plugin under.
            pluginFolder: the plugin's root folder.
            pluginVersion: the plugin's version.
            isUserPlugin: whether the plugin is a user plugin (not maintained by the core Meshroom team).
            registerProviders: True if all the valid providers from the plugin should be registered.
        """
        self._addPlugin(defaultPluginName, pluginFolder, PluginType.PATH, pluginVersion=pluginVersion,
                        isUserPlugin=isUserPlugin, hasMeshroomFolder=True, registerProviders=registerProviders)

    def addPluginFromLocalFolder(self, defaultPluginName: str, pluginFolder: str, registerProviders: bool = True):
        """
        Load a plugin located in the local plugins folder and register its valid providers.

        The plugin's modules are expected in a "meshroom" folder inside "pluginFolder", and its
        process environment is built from that folder's directory tree ("bin"/"lib"/"lib64"/"venv").

        Args:
            defaultPluginName: the default name to register the plugin under.
            pluginFolder: the plugin's root folder.
            registerProviders: True if all the valid providers from the plugin should be registered.
        """
        self._addPlugin(defaultPluginName, pluginFolder, PluginType.LOCAL, pluginVersion=None,
                        isUserPlugin=False, hasMeshroomFolder=True, registerProviders=registerProviders)

    def addPluginFromBuiltInFolder(self, defaultPluginName: str, pluginFolder: str,
                                   registerProviders: bool = True):
        """
        Load a plugin from a built-in Meshroom folder and register its valid providers.

        "pluginFolder" is expected to directly contain the plugin's modules (no nested "meshroom" folder).
        This is how Meshroom's own "nodes"/"submitters" folders are laid out. The plugin is never a user
        plugin.

        Args:
            defaultPluginName: the name to register the plugin under.
            pluginFolder: the plugin's root folder, directly containing its modules.
            registerProviders: True if all the valid providers from the plugin should be registered.
        """
        self._addPlugin(defaultPluginName, pluginFolder, PluginType.BUILTIN, pluginVersion=None,
                        isUserPlugin=False, hasMeshroomFolder=False, registerProviders=registerProviders)

    def removePlugin(self, plugin: Plugin, unregisterProviders: bool = True, unloadPlugin: bool = True):
        """
        Remove a loaded Plugin object.

        Args:
            plugin: the Plugin to remove from the list of loaded plugins.
            unregisterProviders: True if all the providers from the plugin should be unregistered.
            unloadPlugin: True if the plugin virtual package should be unload.
        """
        if self.getPlugin(plugin.name):
            if unregisterProviders:
                for name, nodeDescProvider in plugin.nodeDescProviders.items():
                    if self._nodeDescProviders.get(name) is nodeDescProvider:
                        del self._nodeDescProviders[name]
                for name, submitterProvider in plugin.submitterProviders.items():
                    if self._submitterProviders.get(name) is submitterProvider:
                        del self._submitterProviders[name]
            if unloadPlugin:
                self._pluginLoader.unloadPlugin(plugin.name)
            del self._plugins[plugin.name]

    def registerPluginProviders(self, plugin: Plugin):
        """
        Register every valid node description and submitter provider "plugin" contains.

        Args:
            plugin: the Plugin whose valid providers should be registered.
        """
        for name, nodeDescProvider in plugin.nodeDescProviders.items():
            if nodeDescProvider.status != NodeDescProviderStatus.VALID:
                continue
            if name in self._nodeDescProviders:
                existingProvider = self._nodeDescProviders[name]
                if existingProvider != nodeDescProvider:
                    logging.warning(
                        f"Could not register node {name} ({nodeDescProvider.path}) "
                        f"because another node is already registered with this name ({existingProvider.path})"
                    )
                continue
            self._nodeDescProviders[name] = nodeDescProvider

        for name, submitterProvider in plugin.submitterProviders.items():
            if submitterProvider.status != SubmitterProviderStatus.VALID:
                continue
            if name in self._submitterProviders:
                existingProvider = self._submitterProviders[name]
                if existingProvider != submitterProvider:
                    logging.warning(
                        f"Could not register submitter {name} ({submitterProvider.path}) "
                        f"because another submitter is already registered with this name ({existingProvider.path})"
                    )
                continue
            self._submitterProviders[name] = submitterProvider

    def getPlugins(self) -> dict[str, Plugin]:
        """
        Return a dictionary containing all the loaded Plugins,
        with {key, value} = {name, Plugin}.
        """
        return self._plugins

    def getPlugin(self, name: str) -> Plugin:
        """
        Return the loaded Plugin object with "name".

        Args:
            name: the unique name of the Plugin, used upon its loading.

        Returns:
            Plugin | None: the loaded Plugin object if it exists, None otherwise.
        """
        for plugin in self._plugins.values():
            if plugin.name == name:
                return plugin
        return None

    def getPluginFromNodeDesc(self, name: str) -> Plugin:
        """
        Return the loaded Plugin that contains the node descriptor "name", independently
        from whether it has been registered or not.

        Args:
            name: the name of the node descriptor that needs to be searched for across
                  plugins.

        Returns:
            Plugin | None: the Plugin the node belongs to if it exists, None otherwise.
        """
        for plugin in self._plugins.values():
            if plugin.containsNodeDescProvider(name):
                return plugin
        return None

    def getPipelineTemplates(self) -> dict[str, str]:
        """
        Return a dictionary combining the pipeline templates of every available Plugin,
        with {key, value} = {template name, absolute path}.

        If several plugins provide a template with the same name, only the last one
        encountered is kept.

        Returns:
            dict: The combined templates of every available Plugin.
        """
        templates = {}
        for plugin in self._plugins.values():
            templates.update(plugin.templates)
        return templates

    def isNodeDescRegistered(self, name: str) -> bool:
        """
        Return whether the node descriptor provider has been registered already.

        Args:
            name: the name of the node descriptor whose registration needs to be checked.
        """
        return name in self._nodeDescProviders

    def getNodeDescProviders(self) -> dict[str, NodeDescProvider]:
        """
        Return a dictionary containing all the registered NodeDescProviders,
        with {key, value} = {name, NodeDescProvider}.
        """
        return self._nodeDescProviders

    def getNodeDescProvider(self, name: str) -> NodeDescProvider:
        """
        Return the NodeDescProvider object that has been registered under the name "name" if it exists.

        Args:
            name: the name of the NodeDescProvider.

        Returns:
            NodeDescProvider | None: the registered NodeDescProvider object if it exists, None otherwise.
        """
        if self.isNodeDescRegistered(name):
            return self._nodeDescProviders[name]
        return None

    def isSubmitterRegistered(self, name: str) -> bool:
        """
        Return whether the submitter provider has been registered already.

        Args:
            name: the name of the submitter provider.
        """
        return name in self._submitterProviders

    def getSubmitterProviders(self) -> dict[str, SubmitterProvider]:
        """
        Return a dictionary containing all the registered SubmitterProvider,
        with {key, value} = {name, SubmitterProvider}.
        """
        return self._submitterProviders

    def getSubmitterProvider(self, name: str) -> SubmitterProvider:
        """
        Return the SubmitterProvider object that has been registered under the name "name" if it exists.

        Args:
            name: the name of the SubmitterProvider.

        Returns:
            SubmitterProvider | None: the registered SubmitterProvider object if it exists, None otherwise.
        """
        if self.isSubmitterRegistered(name):
            return self._submitterProviders[name]
        return None

    def getPluginRegistries(self) -> dict[str, PluginRegistry]:
        """
        Return a dictionary containing all the registered PluginRegistry,
        with {key, value} = {name, PluginRegistry}.
        """
        return self._pluginRegistries

    def addPluginRegistryFile(self, filepath: Path, updateRecords: bool = False) -> bool:
        """
        Register a PluginRegistry from a local "<registryName>.json" registry file.
        The registry is skipped if a registry with the same name is already registered.

        Args:
            filepath: the path of a registry file.
            updateRecords: load the registry's records from its file right after creating it.

        Returns:
            bool: whether the registry was read and registered successfully.
        """
        if not self.localPluginsEnabled:
            logging.error(f"Cannot add plugin registry file '{filepath}', local plugin management disabled")
            return False

        # Get registry from registry file
        registry = PluginRegistry(filepath, parent=self)
        if registry.name in self._pluginRegistries:
            logging.warning(f"Plugin registry '{registry.name}' is already registered")
            return False

        # Load registry records
        if updateRecords:
            registry.updateRecords()

        # Add to plugin registries dict
        self._pluginRegistries[registry.name] = registry
        return True

    @Slot()
    @Slot(bool)
    @Slot(bool, bool)
    def refreshPluginRegistries(self, updateRecords: bool = True, useTTL: bool = True) -> None:
        """
        Ensure every plugin registry is up to date with its remote source, re-fetching the ones
        that are not, and optionally reload their records from the (possibly updated) registry files.
        A registry that is already up to date and already holds records is left untouched.

        Args:
            updateRecords: Reload the records of each refreshed registry from its registry file.
            useTTL: Skip re-validation of registries whose TTL has not expired yet.
        """
        if not self.localPluginsEnabled:
            logging.error("Cannot refresh plugin registries, local plugin management disabled")
            return

        for registry in self._pluginRegistries.values():
            if not registry.matchesRemote(useTTL):
                registry.fetch()
            elif len(registry.records) > 0:
                continue
            if updateRecords:
                registry.updateRecords()

    @Slot(BaseObject, result=BaseObject)
    def getUpdateRecord(self, plugin: Plugin) -> Optional[PluginRecord]:
        """
        Return the PluginRecord describing an available update for "plugin", if any.

        An update is available when a registered PluginRecord shares "plugin"'s name and publisher,
        and advertises a different version.

        Args:
            plugin: the installed Plugin to check for an available update.

        Returns:
            PluginRecord | None: the matching record if an update is available, None otherwise.
        """
        for registry in self._pluginRegistries.values():
            record = registry.getRecord(plugin.name)
            if record is not None and record.publisher == plugin.publisher and record.version != plugin.version:
                return record
        return None

    @Slot(result=list)
    @Slot(list, result=list)
    @Slot(list, bool, result=list)
    @Slot(list, bool, bool, result=list)
    @Slot(list, bool, bool, bool, result=list)
    def searchPlugin(self, names: list[str] = None, strict: bool = True,
                     installed: bool = True, available: bool = True) -> list[Plugin | PluginRecord]:
        """
        Return a list containing all the plugins (installed and / or available),
        ordered by name.

        If "names" is provided, only the plugins matching one of the "names" are returned.
        When "strict" is True, a Plugin/PluginRecord's name must be exactly equal to one of the "names".
        When "strict" is False, a Plugin/PluginRecord is returned if its name contains any of the "names"
        as a substring.

        Args:
            names: The plugin names (or substrings) to filter the Plugin/PluginRecord with.
            strict: Whether to match plugin names exactly or as substrings.
            installed: Whether to include the locally installed plugins.
            available: Whether to include the plugins from the external sources.

        Returns:
            list: The matching Plugin / PluginRecord objects, ordered by name.
        """
        plugins: dict[str, Plugin | PluginRecord] = {}
        # Available plugins
        if available:
            for registry in self._pluginRegistries.values():
                for record in registry.records:
                    if record.name in self._plugins:
                        continue
                    plugins[record.name] = record
        # Installed plugins
        if installed:
            for plugin in self._plugins.values():
                plugins[plugin.name] = plugin
        # Search filter
        if names is not None:
            if strict:
                plugins = {name: plugin for name, plugin in plugins.items() if name in names}
            else:
                plugins = {name: plugin for name, plugin in plugins.items() if any(query in name for query in names)}
        # Sort plugins
        return sorted(plugins.values(), key=lambda plugin: plugin.name)
