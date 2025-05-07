from __future__ import annotations

import logging

from pathlib import Path

from meshroom.common import BaseObject
from meshroom.core import desc

class ProcessEnv(BaseObject):
    """
    Describes the environment required by a node's process.
    """

    def __init__(self, folder: str):
        super().__init__()
        self.binPaths: list = [Path(folder, "bin")]
        self.libPaths: list = [Path(folder, "lib"), Path(folder, "lib64")]
        self.pythonPathFolders: list = [Path(folder)] + self.binPaths


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
    """
    def __init__(self, nodeDesc: desc.Node, plugin: Plugin = None):
        super().__init__()
