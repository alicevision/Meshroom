from __future__ import annotations

import logging

from meshroom.common import BaseObject
from meshroom.core.plugins.base import NodeDescProvider, NodeDescProviderStatus, Plugin


class PluginManager(BaseObject):
    """
    Manager for all the loaded Plugin objects as well as the registered NodeDescProvider objects.

    Members:
        plugins: dictionary containing all the loaded Plugins, with their name as the key
        nodeDescProviders: dictionary containing all the NodeDescProviders that have been registered
                      (a NodeDescProvider may exist without having been registered) with their name as
                      the key
    """

    def __init__(self):
        super().__init__()

        self._plugins: dict[str: Plugin] = {}  # loaded plugins
        self._nodeDescProviders: dict[str: NodeDescProvider] = {}  # registered node descriptor providers

    def getPlugins(self) -> dict[str: Plugin]:
        """
        Return a dictionary containing all the loaded Plugins, with {key, value} =
        {name, Plugin}.
        """
        return self._plugins

    def getPlugin(self, name: str, uname: bool = True) -> Plugin:
        """
        Return the loaded Plugin object with "name".

        Args:
            name: the unique name of the Plugin, used upon its loading.
            uname: the name passed as argument is the unique name of the plugin.
                   if set to False, we will search for any plugin with this name
                   but this means there can be a collision. To avoid any confusion
                   use this function with the unique name as much as possible.

        Returns:
            Plugin | None: the loaded Plugin object if it exists, None otherwise.
        """
        if uname:
            # Find plugin with unique name
            if name in self._plugins:
                return self._plugins[name]
        else:
            for plugin in self._plugins.values():
                if plugin.name == name:
                    return plugin
        return None

    def addPlugin(self, plugin: Plugin, registerNodeDescProviders: bool = True):
        """
        Load a Plugin object.

        Args:
            plugin: the Plugin to load and add to the list of loaded plugins.
            registerNodeDescProviders: True if all the NodeDescProviders from the plugin should be
                                 registered at the same time the plugin is being loaded. Otherwise,
                                 the NodeDescProviders will have to be registered at a later occasion.
        """
        pluginUName = plugin.uname
        if self.getPlugin(pluginUName):
            logging.warning(f"Plugin {pluginUName} is already registered.")
            return
        self._plugins[pluginUName] = plugin
        if registerNodeDescProviders:
            for node in plugin.nodes:
                self.registerNode(plugin.nodes[node])

    def removePlugin(self, plugin: Plugin, unregisterNodeDescProviders: bool = True):
        """
        Remove a loaded Plugin object.

        Args:
            plugin: the Plugin to remove from the list of loaded plugins.
            unregisterNodeDescProviders: True if all the nodes from the plugin should be unregistered
                                   (if they are registered) at the same time as the plugin is unloaded.
                                   Otherwise, the registered NodeDescProviders will remain while the
                                   Plugin itself will be unloaded.
        """
        if self.getPlugin(plugin.uname):
            if unregisterNodeDescProviders:
                for node in plugin.nodes.values():
                    self.unregisterNode(node)
            del self._plugins[plugin.uname]

    def belongsToPlugin(self, name: str) -> Plugin:
        """
        Check whether the node descriptor provider belongs to a loaded plugin, independently from
        whether it has been registered or not.

        Args:
            name: the name of the node descriptor provider that needs to be searched for across
                  plugins.

        Returns:
            Plugin | None: the Plugin the node belongs to if it exists, None otherwise.
        """
        for plugin in self._plugins.values():
            if plugin.containsNodeDescProvider(name):
                return plugin
        return None

    def isNodeDescRegistered(self, name: str) -> bool:
        """
        Return whether the node descriptor provider has been registered already.

        Args:
            name: the name of the node descriptor whose registration needs to be checked.
        """
        return name in self._nodeDescProviders

    def getNodeDescProviders(self) -> dict[str: NodeDescProvider]:
        """
        Return a dictionary containing all the registered NodeDescProviders, with
        {key, value} = {name, NodeDescProvider}.
        """
        return self._nodeDescProviders

    def getNodeDescProvider(self, name: str) -> NodeDescProvider:
        """
        Return the NodeDescProvider object that has been registered under the name "name" if it exists.

        Args:
            name: the name of the NodeDescProvider used for its registration.

        Returns:
            NodeDescProvider | None: the loaded NodeDescProvider object if it exists, None otherwise.
        """
        if self.isNodeDescRegistered(name):
            return self._nodeDescProviders[name]
        return None

    def registerNode(self, nodeDescProvider: NodeDescProvider):
        """
        Register a node descriptor provider. A registered node descriptor provider will become
        instantiable. If it is already registered, or if there is an issue with the node description,
        the node descriptor provider will not be registered and its status will be updated.

        Args:
            nodeDescProvider: the node descriptor provider to register.
        """
        name = nodeDescProvider.nodeDescClass.__name__
        if self.isNodeDescRegistered(name):
            existingProvider: NodeDescProvider = self._nodeDescProviders[name]
            logging.warning(
                f"Could not register node {name} ({nodeDescProvider.path}) "
                f"because another node is already registered with this name ({existingProvider.path})"
            )
            return
        if nodeDescProvider.status in (NodeDescProviderStatus.DESC_ERROR,
                                 NodeDescProviderStatus.ERROR):
            logging.warning(
                f"Could not register node {name} ({nodeDescProvider.path}) "
                f"because the node is in error ({nodeDescProvider.status})."
            )
            return

        try:
            self._nodeDescProviders[name] = nodeDescProvider
            nodeDescProvider.status = NodeDescProviderStatus.LOADED
        except Exception as exc:
            logging.error(f"NodeDescProvider {name} could not be loaded: {exc}")
            nodeDescProvider.status = NodeDescProviderStatus.LOADING_ERROR

    def unregisterNode(self, nodeDescProvider: NodeDescProvider):
        """
        Unregister a node descriptor provider. When unregistered, a node descriptor provider cannot be
        instantiated anymore. If it is not registered already, nothing happens.

        Args:
            nodeDescProvider: the node descriptor provider to unregister.
        """
        name = nodeDescProvider.nodeDescClass.__name__
        if self.isNodeDescRegistered(name):
            if nodeDescProvider.status != NodeDescProviderStatus.LOADED:
                logging.warning(f"NodeDescProvider {name} is registered but is not correctly loaded.")
            else:
                nodeDescProvider.status = NodeDescProviderStatus.NOT_LOADED
            del self._nodeDescProviders[name]
