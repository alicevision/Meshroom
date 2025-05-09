from __future__ import annotations

import logging
import os

from enum import Enum
from inspect import getfile
from pathlib import Path

from meshroom.common import BaseObject
from meshroom.core import desc

def validateNodeDesc(nodeDesc: desc.Node) -> list:
    """
    Check that the node has a valid description before being loaded. For the description
    to be valid, the default value of every parameter needs to correspond to the type
    of the parameter.
    An empty returned list means that every parameter is valid, and so is the node's description.
    If it is not valid, the returned list contains the names of the invalid parameters. In case
    of nested parameters (parameters in groups or lists, for example), the name of the parameter
    follows the name of the parent attributes. For example, if the attribute "x", contained in group
    "group", is invalid, then it will be added to the list as "group:x".

    Args:
        nodeDesc: description of the node.

    Returns:
        errors: the list of invalid parameters if there are any, empty list otherwise
    """
    errors = []

    for param in nodeDesc.inputs:
        err = param.checkValueTypes()
        if err:
            errors.append(err)

    for param in nodeDesc.outputs:
        if param.value is None:
            continue
        err = param.checkValueTypes()
        if err:
            errors.append(err)

    return errors


class ProcessEnv(BaseObject):
    """
    Describes the environment required by a node's process.
    """

    def __init__(self, folder: str):
        super().__init__()
        self.binPaths: list = [Path(folder, "bin")]
        self.libPaths: list = [Path(folder, "lib"), Path(folder, "lib64")]
        self.pythonPathFolders: list = [Path(folder)] + self.binPaths


class NodePluginStatus(Enum):
    """
    Loading status for NodePlugin objects.
    """
    NOT_LOADED = 0  # The node plugin exists but is not loaded and cannot be used (not registered)
    LOADED = 1  # The node plugin is currently loaded and functional (it has been registered)
    DESC_ERROR = 2  # The node plugin exists but has an invalid description
    ERROR = 3  # The node plugin exists and is valid but could not be successfully loaded


class Plugin(BaseObject):
    """
    A collection of node plugins.

    Members:
        name: the name of the plugin (e.g. name of the Python module containing the node plugins)
        path: the absolute path of the plugin
        _nodePlugins: dictionary mapping the name of a node plugin contained in the plugin
                      to its corresponding NodePlugin object
        _templates: dictionary mapping the name of templates (.mg files) associated to the plugin
                    with their absolute paths
        processEnv: the environment required for the nodes' processes to be correctly executed
    """

    def __init__(self, name: str, path: str):
        super().__init__()

        self._name: str = name
        self._path: str = path

        self._nodePlugins: dict[str: NodePlugin] = {}
        self._templates: dict[str: str] = {}
        self._processEnv: ProcessEnv = ProcessEnv(path)

        self.loadTemplates()

    @property
    def name(self):
        """ Return the name of the plugin. """
        return self._name

    @property
    def path(self):
        """ Return the absolute path of the plugin. """
        return self._path

    @property
    def templates(self):
        """ Return the list of templates associated to the plugin. """
        return self._templates

    @property
    def processEnv(self):
        """ Return the environment required to successfully execute processes. """
        return self._processEnv

    def addNodePlugin(self, nodePlugin: NodePlugin):
        """
        Add a node plugin to the current plugin object and assign it as its containing plugin.
        The node plugin is added to the dictionary of node plugins with the name of the node
        descriptor as its key.

        Args:
            nodePlugin: the NodePlugin object to add to the Plugin.
        """
        self._nodePlugins[nodePlugin.nodeDescriptor.__name__] = nodePlugin
        nodePlugin.plugin = self

    def removeNodePlugin(self, name: str):
        """
        Remove a node plugin from the current plugin object and delete any container relationship.

        Args:
            name: the name of the NodePlugin to remove.
        """
        if name in self._nodePlugins:
            self._nodePlugins[name].plugin = None
            del self._nodePlugins[name]
        else:
            logging.warning(f"Node plugin {name} is not part of the plugin {self.name}.")

    def loadTemplates(self):
        """
        Load all the pipeline templates that are available within the plugin folder.
        Whenever this method is called, the list of templates for the plugin is cleared,
        before being filled again.
        """
        self._templates.clear()
        for file in os.listdir(self.path):
            if file.endswith(".mg"):
                self._templates[os.path.splitext(file)[0]] = os.path.join(self.path, file)


class NodePlugin(BaseObject):
    """
    Based on a node description, a NodePlugin represents a loadable node.

    Members:
        plugin: the Plugin object that contains this node plugin
        path: absolute path to the file containing the node's description
        nodeDescriptor: the description of the node
        status: the loading status on the node plugin
        errors: the list of errors (if there are any) when validating the description
                of the node or attempting to load it
        processEnv: the environment required for the node plugin's process. It can either
                    be specific to this node plugin, or be common for all the node plugins within
                    the plugin
    """

    def __init__(self, nodeDesc: desc.Node, plugin: Plugin = None):
        super().__init__()
        self.plugin: Plugin = plugin
        self.path: str = Path(getfile(nodeDesc)).resolve().as_posix()
        self.nodeDescriptor: desc.Node = nodeDesc

        self.status: NodePluginStatus = NodePluginStatus.NOT_LOADED
        self.errors: list[str] = validateNodeDesc(nodeDesc)

        if self.errors:
            self.status = NodePluginStatus.DESC_ERROR

        self._processEnv = None

    @property
    def plugin(self):
        """
        Return the Plugin object that contains this node plugin.
        If the node plugin has not been assigned to a plugin yet, this value will
        be set to None.
        """
        return self._plugin

    @plugin.setter
    def plugin(self, plugin: Plugin):
        self._plugin = plugin

    @property
    def processEnv(self):
        """"
        Return the process environment that is specific to the node plugin if it has any.
        Otherwise, the Plugin's is returned.
        """
        if self._processEnv:
            return self._processEnv
        if self.plugin:
            return self.plugin.processEnv
        return None


class NodePluginManager(BaseObject):
    """
    Manager for all the loaded Plugin objects as well as the registered NodePlugin objects.

    Members:
        _plugins: dictionary containing all the loaded Plugins, with their name as the key
        _nodePlugins: dictionary containing all the NodePlugins that have been registered
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

    def getPlugins(self) -> dict[str: Plugin]:
        """
        Return a dictionary containing all the loaded Plugins, with {key, value} =
        {name, Plugin}.
        """
        return self._plugins

    def getPlugin(self, name: str) -> Plugin:
        """
        Return the loaded Plugin object named "name".

        Args:
            name: the name of the Plugin, used upon its loading.

        Returns:
            Plugin | None: the loaded Plugin object if it exists, None otherwise.
        """
        if name in self._plugins:
            return self._plugins[name]
        return None

    def addPlugin(self, plugin: Plugin):
        """
        Load a Plugin object.

        Args:
            plugin: the Plugin to load and add to the list of loaded plugins.
        """
        if not self.getPlugin(plugin.name):
            self._plugins[plugin.name] = plugin

    def getNodePlugins(self) -> dict[str: NodePlugin]:
        """
        Return a dictionary containing all the registered NodePlugins, with
        {key, value} = {name, NodePlugin}.
        """
        return self._nodePlugins

    def getNodePlugin(self, name: str) -> NodePlugin:
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

    def registerPlugin(self, name: str):
        """
        Register all the NodePlugins contained in the Plugin loaded as "name".

        Args:
           name: the name of the Plugin whose NodePlugins will be registered.
        """
        plugin = self.getPlugin(name)
        if plugin:
            for node in plugin._nodePlugins:
                self.registerNode(plugin._nodePlugins[node])
        else:
            logging.error(f"No loaded Plugin named {name}.")

    def registerNode(self, nodePlugin: NodePlugin):
        """
        Register a node plugin. A registered node plugin will become instantiable.
        If it is already registered, or if there is an issue with the node description,
        the node plugin will not be registered and its status will be updated.

        Args:
            nodePlugin: the node plugin to register.
        """
        name = nodePlugin.nodeDescriptor.__name__
        if not self.isRegistered(name) and nodePlugin.status != NodePluginStatus.DESC_ERROR:
            try:
                self._nodePlugins[name] = nodePlugin
                nodePlugin.status = NodePluginStatus.LOADED
            except Exception as e:
                logging.error(f"NodePlugin {name} could not be loaded: {e}")
                nodePlugin.status = NodePluginStatus.ERROR

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
            del self._nodePlugins[name]
            nodePlugin.status = NodePluginStatus.NOT_LOADED
