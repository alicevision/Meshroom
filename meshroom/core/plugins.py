from __future__ import annotations

import logging

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
        _nodePlugins: dictionary mapping the name of a node plugin to its corresponding
                      NodePlugin object
        processEnv: the environment required for the nodes' processes to be correctly executed
    """

    def __init__(self, name: str, path: str):
        super().__init__()

        self._name: str = name
        self._path: str = path

        self._nodePlugins: dict[str: NodePlugin] = {}
        self._processEnv: ProcessEnv = ProcessEnv(path)

    @property
    def name(self):
        """ Return the name of the plugin. """
        return self._name

    @property
    def path(self):
        """ Return the absolute path of the plugin. """
        return self._path

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
