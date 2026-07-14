from __future__ import annotations

import logging

from meshroom.common import BaseObject
from meshroom.core.plugins.base import NodePlugin, NodePluginStatus, Plugin


class NodePluginManager(BaseObject):
    """
    Manager for all the loaded Plugin objects as well as the registered NodePlugin objects.

    Members:
        plugins: dictionary containing all the loaded Plugins, with their name as the key
        nodePlugins: dictionary containing all the NodePlugins that have been registered
                      (a NodePlugin may exist without having been registered) with their name as
                      the key
    """

    def __init__(self):
        super().__init__()

        self._plugins: dict[str: Plugin] = {}  # loaded plugins
        self._nodePlugins: dict[str: NodePlugin] = {}  # registered node plugins

    def isRegistered(self, name: str) -> bool:
        """
        Return whether the node plugin has been registered already.

        Args:
            name: the name of the node plugin whose registration needs to be checked.
        """
        return name in self._nodePlugins

    def belongsToPlugin(self, name: str) -> Plugin:
        """
        Check whether the node plugin belongs to a loaded plugin, independently from
        whether it has been registered or not.

        Args:
            name: the name of the node plugin that needs to be searched for across plugins.

        Returns:
            Plugin | None: the Plugin the node belongs to if it exists, None otherwise.
        """
        for plugin in self._plugins.values():
            if plugin.containsNodePlugin(name):
                return plugin
        return None

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

    def addPlugin(self, plugin: Plugin, registerNodePlugins: bool = True):
        """
        Load a Plugin object.

        Args:
            plugin: the Plugin to load and add to the list of loaded plugins.
            registerNodePlugins: True if all the NodePlugins from the plugin should be registered
                                 at the same time the plugin is being loaded. Otherwise, the
                                 NodePlugins will have to be registered at a later occasion.
        """
        pluginUName = plugin.uname
        if self.getPlugin(pluginUName):
            logging.warning(f"Plugin {pluginUName} is already registered.")
            return
        self._plugins[pluginUName] = plugin
        if registerNodePlugins:
            for node in plugin.nodes:
                self.registerNode(plugin.nodes[node])

    def removePlugin(self, plugin: Plugin, unregisterNodePlugins: bool = True):
        """
        Remove a loaded Plugin object.

        Args:
            plugin: the Plugin to remove from the list of loaded plugins.
            unregisterNodePlugins: True if all the nodes from the plugin should be unregistered (if they
                                   are registered) at the same time as the plugin is unloaded. Otherwise,
                                   the registered NodePlugins will remain while the Plugin itself will
                                   be unloaded.
        """
        if self.getPlugin(plugin.uname):
            if unregisterNodePlugins:
                for node in plugin.nodes.values():
                    self.unregisterNode(node)
            del self._plugins[plugin.uname]

    def getRegisteredNodePlugins(self) -> dict[str: NodePlugin]:
        """
        Return a dictionary containing all the registered NodePlugins, with
        {key, value} = {name, NodePlugin}.
        """
        return self._nodePlugins

    def getRegisteredNodePlugin(self, name: str) -> NodePlugin:
        """
        Return the NodePlugin object that has been registered under the name "name" if it exists.

        Args:
            name: the name of the NodePlugin used for its registration.

        Returns:
            NodePlugin | None: the loaded NodePlugin object if it exists, None otherwise.
        """
        if self.isRegistered(name):
            return self._nodePlugins[name]
        return None

    def registerNode(self, nodePlugin: NodePlugin):
        """
        Register a node plugin. A registered node plugin will become instantiable.
        If it is already registered, or if there is an issue with the node description,
        the node plugin will not be registered and its status will be updated.

        Args:
            nodePlugin: the node plugin to register.
        """
        name = nodePlugin.nodeDescriptor.__name__
        if self.isRegistered(name):
            existingPlugin: NodePlugin = self._nodePlugins[name]
            logging.warning(
                f"Could not register node {name} ({nodePlugin.path}) "
                f"because another node is already registered with this name ({existingPlugin.path})"
            )
            return
        if nodePlugin.status in (NodePluginStatus.DESC_ERROR,
                                 NodePluginStatus.ERROR):
            logging.warning(
                f"Could not register node {name} ({nodePlugin.path}) "
                f"because the node is in error ({nodePlugin.status})."
            )
            return

        try:
            self._nodePlugins[name] = nodePlugin
            nodePlugin.status = NodePluginStatus.LOADED
        except Exception as exc:
            logging.error(f"NodePlugin {name} could not be loaded: {exc}")
            nodePlugin.status = NodePluginStatus.LOADING_ERROR

    def unregisterNode(self, nodePlugin: NodePlugin):
        """
        Unregister a node plugin. When unregistered, a node plugin cannot be instantiated anymore.
        If it is not registered already, nothing happens.

        Args:
            nodePlugin: the node plugin to unregister.
        """
        name = nodePlugin.nodeDescriptor.__name__
        if self.isRegistered(name):
            if nodePlugin.status != NodePluginStatus.LOADED:
                logging.warning(f"NodePlugin {name} is registered but is not correctly loaded.")
            else:
                nodePlugin.status = NodePluginStatus.NOT_LOADED
            del self._nodePlugins[name]
