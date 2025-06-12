from __future__ import annotations

import importlib
import logging
import os
import sys

from enum import Enum
from inspect import getfile
from pathlib import Path

from meshroom.common import BaseObject
from meshroom.core import desc
from meshroom.core.desc.node import _MESHROOM_ROOT

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


class ProcessEnvType(Enum):
    """ Supported process environments. """
    DEFAULT = "default",
    CONDA = "conda",
    VIRTUALENV = "virtualenv",
    REZ = "rez"


class ProcessEnv(BaseObject):
    """
    Describes the environment required by a node's process.

    Args:
        folder: the source folder for the process.
        envType: (optional) the type of process environment.
        uri: (optional) the Unique Resource Identifier to activate the environment.
    """

    def __init__(self, folder: str, envType: ProcessEnvType = ProcessEnvType.DEFAULT):
        super().__init__()
        self._folder = folder
        self._processEnvType: ProcessEnvType = envType
        self.uri = ""

    def getEnvDict(self) -> dict:
        """ Return the environment dictionary if it has been modified, None otherwise. """
        return None

    def getCommandPrefix(self) -> str:
        """ Return the prefix to the command line that will be executed by the process. """
        return ""

    def getCommandSuffix(self) -> str:
        """ Return the suffix to the command line that will be executed by the process. """
        return ""


class DirTreeProcessEnv(ProcessEnv):
    """
    """
    def __init__(self, folder: str, envType: ProcessEnvType = ProcessEnvType.DEFAULT, uri: str = ""):
        if envType == ProcessEnvType.REZ:
            raise RuntimeError("Wrong process environment type.")
        if not uri and envType != ProcessEnvType.DEFAULT:
            raise RuntimeError("URI should be provided for the process environment.")

        super().__init__(folder, envType)

        self.uri = uri
        self.binPaths: list = [str(Path(folder, "bin"))]
        self.libPaths: list = [str(Path(folder, "lib")), str(Path(folder, "lib64"))]
        self.pythonPaths: list = [str(Path(folder))] + self.binPaths

    def getEnvDict(self) -> dict:
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{_MESHROOM_ROOT}{os.pathsep}{os.pathsep.join(self.pythonPaths)}{os.pathsep}{os.getenv('PYTHONPATH', '')}"
        env["LD_LIBRARY_PATH"] = f"{os.pathsep.join(self.libPaths)}{os.pathsep}{os.getenv('LD_LIBRARY_PATH', '')}"
        env["PATH"] = f"{os.pathsep.join(self.binPaths)}{os.pathsep}{os.getenv('PATH', '')}"
        # env["PYTHONPATH"] = f"{_MESHROOM_ROOT}{os.pathsep}{os.pathsep.join(self.pythonPaths)}"
        # env["LD_LIBRARY_PATH"] = f"{os.pathsep.join(self.libPaths)}"
        # env["PATH"] = f"{os.pathsep.join(self.binPaths)}"

        return env

    def getCommandPrefix(self) -> str:
        if self._processEnvType == ProcessEnvType.CONDA:
            return f"conda run -n {self.uri} "
        if self._processEnvType == ProcessEnvType.VIRTUALENV:
            return f"{self.uri}/bin/python "
        return super().getCommandPrefix()


class RezProcessEnv(ProcessEnv):
    """
    """
    def __init__(self, folder: str, envType: ProcessEnvType = ProcessEnvType.REZ, uri: str = ""):
        if envType != ProcessEnvType.REZ:
            raise RuntimeError("Wrong process environment type.")
        if not uri:
            raise RuntimeError("Wrong URI for Rez environment process.")

        super().__init__(folder, envType)
        self.uri = uri
    def getEnvDict(self):
        env = os.environ.copy()

        return env

    def getCommandPrefix(self):
        if Path(self.uri).exists() and Path(self.uri).suffix == ".rxt":
            return f"rez env -i {self.uri} -c '"
        return f"rez env {self.uri} -c '"

    def getCommandSuffix(self):
        return "'"


def processEnvFactory(folder: str, envType: str = "default", uri: str = "") -> ProcessEnv:
    if envType == "default":
        return DirTreeProcessEnv(folder)
    if envType == "conda":
        return DirTreeProcessEnv(folder, ProcessEnvType.CONDA, uri)
    if envType == "virtualenv":
        return DirTreeProcessEnv(folder, ProcessEnvType.VIRTUALENV, uri)
    return RezProcessEnv(folder, ProcessEnvType.REZ, uri)


class NodePluginStatus(Enum):
    """
    Loading status for NodePlugin objects.
    """
    NOT_LOADED = 0  # The node plugin exists but is not loaded and cannot be used (not registered)
    LOADED = 1  # The node plugin is currently loaded and functional (it has been registered)
    DESC_ERROR = 2  # The node plugin exists but has an invalid description
    LOADING_ERROR = 3  # The node plugin exists and is valid but could not be successfully registered
    ERROR = 4  # Error when importing the node plugin from its module


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
    def nodes(self):
        """
        Return the dictionary containing the NodePlugin objects associated to
        the plugin.
        """
        return self._nodePlugins

    @property
    def templates(self):
        """ Return the list of templates associated to the plugin. """
        return self._templates

    @property
    def processEnv(self):
        """ Return the environment required to successfully execute processes. """
        return self._processEnv

    @processEnv.setter
    def processEnv(self, processEnv: ProcessEnv):
        self._processEnv = processEnv
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

    def containsNodePlugin(self, name: str) -> bool:
        """
        Return whether the node plugin "name" is part of the plugin, independently from its
        status.

        Args:
            name: the name of the node plugin to be checked.
        """
        return name in self._nodePlugins


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
        timestamp: the timestamp corresponding to the last time the node description's file has been
                   modified
    """

    def __init__(self, nodeDesc: desc.Node, plugin: Plugin = None):
        super().__init__()
        self.plugin: Plugin = plugin
        self.path: str = Path(getfile(nodeDesc)).resolve().as_posix()
        self.nodeDescriptor: desc.Node = nodeDesc
        self.nodeDescriptor.plugin = self

        self.status: NodePluginStatus = NodePluginStatus.NOT_LOADED
        self.errors: list[str] = validateNodeDesc(nodeDesc)

        if self.errors:
            self.status = NodePluginStatus.DESC_ERROR

        self._processEnv = None
        self._timestamp = os.path.getmtime(self.path)

    def reload(self) -> bool:
        """
        Reload the node plugin and update its status accordingly. If the timestamp of the node plugin's
        path has not changed since the last time the plugin has been loaded, then nothing will happen.

        Returns:
            bool: True if the node plugin has successfully been reloaded (i.e. there was no error, and
                  some changes were made since its last loading), False otherwise.
        """
        timestamp = 0.0
        try:
            timestamp = os.path.getmtime(self.path)
        except FileNotFoundError:
            self.status = NodePluginStatus.ERROR
            logging.error(f"[Reload] {self.nodeDescriptor.__name__}: The path at {self.path} was not "
                           "not found.")
            return False

        if self._timestamp == timestamp:
            logging.info(f"[Reload] {self.nodeDescriptor.__name__}: Not reloading. The node description "
                         f"at {self.path} has not been modified since the last load.")
            return False

        updated = importlib.reload(sys.modules.get(self.nodeDescriptor.__module__))
        descriptor = getattr(updated, self.nodeDescriptor.__name__)

        if not descriptor:
            self.status = NodePluginStatus.ERROR
            logging.error(f"[Reload] {self.nodeDescriptor.__name__}: The node description at {self.path} "
                           "was not found.")
            return False

        self.errors = validateNodeDesc(descriptor)
        if self.errors:
            self.status = NodePluginStatus.DESC_ERROR
            logging.error(f"[Reload] {self.nodeDescriptor.__name__}: The node description at {self.path} "
                           "has description errors.")
            return False

        self.nodeDescriptor = descriptor
        self._timestamp = timestamp
        self.status = NodePluginStatus.NOT_LOADED
        logging.info(f"[Reload] {self.nodeDescriptor.__name__}: Successful reloading.")
        return True

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

    @property
    def runtimeEnv(self) -> dict:
        """ Return the environment dictionary for the runtime. """
        return self.processEnv.getEnvDict()


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

    def addPlugin(self, plugin: Plugin, registerNodePlugins: bool = True):
        """
        Load a Plugin object.

        Args:
            plugin: the Plugin to load and add to the list of loaded plugins.
            registerNodePlugins: True if all the NodePlugins from the plugin should be registered
                                 at the same time the plugin is being loaded. Otherwise, the
                                 NodePlugins will have to be registered at a later occasion.
        """
        if not self.getPlugin(plugin.name):
            self._plugins[plugin.name] = plugin
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
        if self.getPlugin(plugin.name):
            if unregisterNodePlugins:
                for node in plugin.nodes.values():
                    self.unregisterNode(node)
            del self._plugins[plugin.name]

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
        if not self.isRegistered(name) and nodePlugin.status not in (NodePluginStatus.DESC_ERROR,
                                                                     NodePluginStatus.ERROR):
            try:
                self._nodePlugins[name] = nodePlugin
                nodePlugin.status = NodePluginStatus.LOADED
            except Exception as e:
                logging.error(f"NodePlugin {name} could not be loaded: {e}")
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
