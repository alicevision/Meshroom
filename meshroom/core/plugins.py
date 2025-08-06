from __future__ import annotations

import glob
import importlib
import json
import logging
import os
import re
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
    DIRTREE = "dirtree",
    REZ = "rez"


class ProcessEnv(BaseObject):
    """
    Describes the environment required by a node's process.

    Args:
        folder: the source folder for the process.
        envType: (optional) the type of process environment.
        uri: (optional) the Unique Resource Identifier to activate the environment.
    """

    def __init__(self, folder: str, envType: ProcessEnvType = ProcessEnvType.DIRTREE, uri: str = ""):
        super().__init__()
        self._folder: str = folder
        self._processEnvType: ProcessEnvType = envType
        self.uri: str = uri

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
    def __init__(self, folder: str):
        super().__init__(folder, ProcessEnvType.DIRTREE)

        venvLibPaths = glob.glob(f'{folder}/lib*/python[0-9].[0-9]*/site-packages', recursive=False)

        self.binPaths: list = [str(Path(folder, "bin"))]
        self.libPaths: list = [str(Path(folder, "lib")), str(Path(folder, "lib64"))]
        self.pythonPaths: list = [str(Path(folder))] + self.binPaths + venvLibPaths

        if sys.platform == "win32":
            # For Windows platforms, try and include the content of the virtual env if it exists
            # The virtual env is expected to be named "venv"
            venvPath = Path(folder, "venv", "Lib", "site-packages")
            if venvPath.exists():
                self.pythonPaths.append(venvPath.as_posix())
        else:
            # For Linux platforms, lib paths may need to be discovered recursively to be properly
            # added to LD_LIBRARY_PATH
            extraLibPaths = []
            regex = re.compile(r"^lib(\d{2})?$")
            for venvPath in venvLibPaths:
                for path, directories, _ in os.walk(venvPath):
                    for directory in directories:
                        if re.match(regex, directory):
                            extraLibPaths.append(os.path.join(path, directory))
            self.libPaths = self.libPaths + extraLibPaths

    def getEnvDict(self) -> dict:
        env = os.environ.copy()
        env["PYTHONPATH"] = os.pathsep.join([f"{_MESHROOM_ROOT}"] + self.pythonPaths + [f"{os.getenv('PYTHONPATH', '')}"])
        env["LD_LIBRARY_PATH"] = f"{os.pathsep.join(self.libPaths)}{os.pathsep}{os.getenv('LD_LIBRARY_PATH', '')}"
        env["PATH"] = f"{os.pathsep.join(self.binPaths)}{os.pathsep}{os.getenv('PATH', '')}"

        return env


class RezProcessEnv(ProcessEnv):
    """
    """
    def __init__(self, folder: str, uri: str = ""):
        if not uri:
            raise RuntimeError("Missing name of the Rez environment needs to be provided.")
        super().__init__(folder, ProcessEnvType.REZ, uri)

    def resolveRezSubrequires(self) -> list[str]:
        """
        Return the list of packages defined for the node execution. These execution packages are named
        subrequires.
        Note: If a package does not have a version number, the version is aligned with the main Meshroom
        environment (if this package is defined).
        """
        subrequires = os.environ.get(f"{self.uri.upper()}_SUBREQUIRES", "").split(os.pathsep)
        packages = []

        # Packages that are resolved in the current environment
        currentEnvPackages = []
        if "REZ_REQUEST" in os.environ:
            resolvedPackages = os.getenv("REZ_RESOLVE", "").split()
            resolvedVersions = {}
            for package in resolvedPackages:
                if package.startswith("~"):
                    continue
                version = package.split("-")
                resolvedVersions[version[0]] = version[1]
            currentEnvPackages = [package + "-" + resolvedVersions[package] for package in resolvedVersions.keys()]
        logging.debug("Packages in the current environment: " + ", ".join(currentEnvPackages))

        # Take packages with the set versions for those which have one, and try to take packages in the current
        # environment (if they are resolved in it)
        for package in subrequires:
            if "-" in package:
                packages.append(package)
            else:
                definedInParentEnv = False
                for p in currentEnvPackages:
                    if p.startswith(package + "-"):
                        packages.append(p)
                        definedInParentEnv = True
                        break
                if not definedInParentEnv:
                    packages.append(package)

        logging.debug("Packages for the execution environment: " + ", ".join(packages))
        return packages

    def getCommandPrefix(self):
        # TODO: make Windows-compatible

        # Use the PYTHONPATH from the subrequires' environment (which will only be resolved once
        # inside the execution environment) and add MESHROOM_ROOT and the plugin's folder itself
        # to it
        pythonPaths = f"{os.pathsep.join(['$PYTHONPATH', f'{_MESHROOM_ROOT}', f'{self._folder}'])}"

        return f"rez env {' '.join(self.resolveRezSubrequires())} -c 'PYTHONPATH={pythonPaths} "

    def getCommandSuffix(self):
        return "'"


def processEnvFactory(folder: str, envType: str = "dirtree", uri: str = "") -> ProcessEnv:
    if envType == "dirtree":
        return DirTreeProcessEnv(folder)
    return RezProcessEnv(folder, uri=uri)


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
        nodePlugins: dictionary mapping the name of a node plugin contained in the plugin
                     to its corresponding NodePlugin object
        templates: dictionary mapping the name of templates (.mg files) associated to the plugin
                   with their absolute paths
        configEnv: the environment variables and their values, as described in the plugin's
                   configuration file
        processEnv: the environment required for the nodes' processes to be correctly executed
    """

    def __init__(self, name: str, path: str):
        super().__init__()

        self._name: str = name
        self._path: str = path

        self._nodePlugins: dict[str: NodePlugin] = {}
        self._templates: dict[str: str] = {}
        self._configEnv: dict[str: str] = {}
        self._processEnv: ProcessEnv = ProcessEnv(path, self._configEnv)

        self.loadTemplates()
        self.loadConfig()

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
        """ Set the environment required to successfully execute processes. """
        self._processEnv = processEnv

    @property
    def configEnv(self):
        """
        Return the dictionary containing the environment variables and their values
        provided in the plugin's configuration file.
        """
        return self._configEnv

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

    def loadConfig(self):
        """
        Load the plugin's configuration file if it exists and saves all its environment variables
        and their values, if they are valid.
        The configuration file is expected to be named "config.json", located at the top-level of
        the plugin.
        """
        try:
            with open(os.path.join(self.path, "config.json")) as config:
                content = json.load(config)
                for entry in content:
                    # An entry is expected to be formatted as follows:
                    # { "key": "key_of_var", "type": "type_of_value", "value": "var_value" }
                    # If "type" is not provided, it is assumed to be "string"
                    k = entry.get("key", None)
                    t = entry.get("type", None)
                    val = entry.get("value", None)

                    if not k or not val:
                        logging.warning(f"Invalid entry in configuration file for {self.name}: {entry}.")
                        continue

                    if t == "path":
                        if os.path.isabs(val):
                            resolvedPath = Path(val).resolve()
                        else:
                            resolvedPath = Path(os.path.join(self.path, val)).resolve()

                        if resolvedPath.exists():
                            val = resolvedPath.as_posix()
                        else:
                            logging.warning(f"{k}: {resolvedPath.as_posix()} does not exist "
                                            f"(path before resolution: {val}).")

                    self._configEnv[k] = str(val)

        except FileNotFoundError:
            logging.debug(f"No configuration file 'config.json' was found for {self.name}.")
        except json.JSONDecodeError as err:
            logging.error(f"Malformed JSON in the configuration file for {self.name}: {err}")
        except IOError as err:
            logging.error(f"Error while accessing the configuration file for {self.name}: {err}")

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
                          f"not found.")
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
                          f"was not found.")
            return False

        self.errors = validateNodeDesc(descriptor)
        if self.errors:
            self.status = NodePluginStatus.DESC_ERROR
            logging.error(f"[Reload] {self.nodeDescriptor.__name__}: The node description at {self.path} "
                          f"has description errors.")
            return False

        self.nodeDescriptor = descriptor
        self.nodeDescriptor.plugin = self
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
        """ Assign this node plugin to a containing Plugin object. """
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

    @property
    def commandPrefix(self) -> str:
        """ Return the command prefix for the NodePlugin's execution. """
        return self.processEnv.getCommandPrefix()

    @property
    def commandSuffix(self) -> str:
        """ Return the command suffix for the NodePlugin's execution. """
        return self.processEnv.getCommandSuffix()


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
