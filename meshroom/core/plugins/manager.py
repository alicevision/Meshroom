from __future__ import annotations

import importlib
import json
import logging
import os
import sys

from enum import Enum
from inspect import getfile
from pathlib import Path

from meshroom.common import BaseObject
from meshroom.core import desc
from meshroom.core.desc.attribute import ValueTypeErrors
from meshroom.core.plugins.env import ProcessEnv


def validateNodeDesc(nodeDesc: desc.BaseNode) -> list[tuple[str, ValueTypeErrors]]:
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
        nodeDesc: Description of the node.

    Returns:
        errors: The list of invalid parameters if there are any, empty list otherwise.
    """
    errors = []

    for param in nodeDesc.inputs:
        errMsg, errType = param.checkValueTypes()
        if errMsg:
            errors.append((errMsg, errType))

    for param in nodeDesc.outputs:
        if param.value is None:
            if issubclass(nodeDesc, desc.InitNode):
                errors.append((f"{param.name}", ValueTypeErrors.DYNAMIC_OUTPUT))
            continue
        errMsg, errType = param.checkValueTypes()
        if errMsg:
            errors.append((errMsg, errType))

    return errors

def formatNodeDescriptionErrorMessage(error: tuple[str, ValueTypeErrors]) -> str:
    """
    Format a node description error message from a tuple containing the error message (name of the attribute) and type.

    Args:
        error: Tuple containing the name of the parameter that was rejected, and the type of the error.

    Returns:
        str: Formatted error message.
    """
    errMsg, errType = error

    if errType == ValueTypeErrors.TYPE:
        return f"'value': Invalid type for parameter '{errMsg}'."
    if errType == ValueTypeErrors.RANGE:
        return f"'range': Invalid range value for parameter '{errMsg}'."
    if errType == ValueTypeErrors.DYNAMIC_OUTPUT:
        return f"'value': Unsupported dynamic output for parameter '{errMsg}'."
    return f"Unknown error for parameter '{errMsg}'."


class NodeProviderStatus(Enum):
    """
    Loading status for NodeProvider objects.
    """
    NOT_LOADED = 0  # The node provider exists but is not loaded and cannot be used
    LOADED = 1  # The node provider is currently loaded and functional
    DESC_ERROR = 2  # The node provider exists but has an invalid description
    LOADING_ERROR = 3  # The node provider exists and is valid but could not be successfully loaded
    ERROR = 4  # Error when importing the node provider from its module


class NodeProvider(BaseObject):
    """
    Based on a node description, a NodeProvider represents a loadable node.

    Members:
        plugin: the Plugin object that contains this node provider
        path: absolute path to the file containing the node's description
        nodeDescriptor: the description of the node
        status: the loading status on the node provider
        errors: the list of errors (if there are any) when validating the description
                of the node or attempting to load it
        processEnv: the environment required for the node provider's process. It can either
                    be specific to this node provider, or be common for all the node providers within
                    the plugin
        timestamp: the timestamp corresponding to the last time the node description's file has been
                   modified
    """

    def __init__(self, nodeDesc: desc.BaseNode, plugin: Plugin = None):
        super().__init__()
        self.plugin: Plugin = plugin
        self.path: str = Path(getfile(nodeDesc)).resolve().as_posix()
        self.nodeDescriptor: desc.BaseNode = nodeDesc
        self.nodeDescriptor.provider = self

        self.status: NodeProviderStatus = NodeProviderStatus.NOT_LOADED
        self.errors: list[tuple[str, ValueTypeErrors]] = validateNodeDesc(nodeDesc)

        if self.errors:
            self.status = NodeProviderStatus.DESC_ERROR

        self._processEnv = None
        self._timestamp = os.path.getmtime(self.path)

    def reload(self) -> bool:
        """
        Reload the node provider and update its status accordingly. If the timestamp of the node provider's
        path has not changed since the last time the plugin has been loaded, then nothing will happen.

        Returns:
            bool: True if the node provider has successfully been reloaded (i.e. there was no error, and
                  some changes were made since its last loading), False otherwise.
        """
        timestamp = 0.0
        try:
            timestamp = os.path.getmtime(self.path)
        except FileNotFoundError:
            self.status = NodeProviderStatus.ERROR
            logging.error(f"[Reload] {self.nodeDescriptor.__name__}: The path at {self.path} was not "
                          f"not found.")
            return False

        if self._timestamp == timestamp:
            logging.info(f"[Reload] {self.nodeDescriptor.__name__}: Not reloading. The node description "
                         f"at {self.path} has not been modified since the last load.")
            return False

        try:
            updated = importlib.reload(sys.modules.get(self.nodeDescriptor.__module__))
        except Exception as exc:
            logging.error(f"[Reload] {self.nodeDescriptor.__name__}: {exc} ({type(exc).__name__})")
            self.status = NodeProviderStatus.DESC_ERROR
            return False
        descriptor = getattr(updated, self.nodeDescriptor.__name__)

        if not descriptor:
            self.status = NodeProviderStatus.ERROR
            logging.error(f"[Reload] {self.nodeDescriptor.__name__}: The node description at {self.path} "
                          f"was not found.")
            return False

        self.errors = validateNodeDesc(descriptor)
        if self.errors:
            self.status = NodeProviderStatus.DESC_ERROR
            logging.error(f"[Reload] {self.nodeDescriptor.__name__}: The node description at {self.path} "
                          f"has description errors.")
            return False

        self.nodeDescriptor = descriptor
        self.nodeDescriptor.provider = self
        self._timestamp = timestamp
        self.status = NodeProviderStatus.NOT_LOADED
        logging.info(f"[Reload] {self.nodeDescriptor.__name__}: Successful reloading.")
        return True

    @property
    def plugin(self):
        """
        Return the Plugin object that contains this node provider.
        If the node provider has not been assigned to a plugin yet, this value will
        be set to None.
        """
        return self._plugin

    @plugin.setter
    def plugin(self, plugin: Plugin):
        """ Assign this node provider to a containing Plugin object. """
        self._plugin = plugin

    @property
    def isUserPlugin(self):
        """ Return whether the node plugin belongs to a user plugin. """
        if self.plugin:
            return self.plugin.isUserPlugin
        return False

    @property
    def processEnv(self):
        """"
        Return the process environment that is specific to the node provider if it has any.
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
        """ Return the command prefix for the NodeProvider's execution. """
        if not self.processEnv:
            return ""
        return self.processEnv.getCommandPrefix()

    @property
    def commandSuffix(self) -> str:
        """ Return the command suffix for the NodeProvider's execution. """
        if not self.processEnv:
            return ""
        return self.processEnv.getCommandSuffix()

    @property
    def configFullEnv(self) -> dict[str: str]:
        """ Return the plugin's full environment dictionary. """
        if not self.plugin:
            return {}
        return self.plugin.configFullEnv


class Plugin(BaseObject):
    """
    A collection of node providers.

    Members:
        name: the name of the plugin (e.g. name of the Python module containing the node providers)
        path: the absolute path of the plugin
        user: whether the plugin is a user plugin (not maintained by the core Meshroom team)
        nodeProviders: dictionary mapping the name of a node provider contained in the plugin
                     to its corresponding NodeProvider object
        templates: dictionary mapping the name of templates (.mg files) associated to the plugin
                   with their absolute paths
        configEnv: the environment variables and their values, as described in the plugin's
                   configuration file
        configFullEnv: the static merge of os.environ and configEnv, with os.environ taking precedence
        processEnv: the environment required for the nodes' processes to be correctly executed
    """
    
    _instancesCount = 0

    def __init__(self, name: str, path: str):
        super().__init__()

        Plugin._instancesCount += 1
        self._uid: str = f"{Plugin._instancesCount:04d}"
        self._name: str = name
        self._path: str = path
        self._user: bool = False

        self._nodeProviders: dict[str: NodeProvider] = {}
        self._templates: dict[str: str] = {}
        self._configEnv: dict[str: str] = {}
        self._configFullEnv: dict[str: str] = {}
        self._processEnv: ProcessEnv = ProcessEnv(path, self._configEnv, self._name)

        self.loadTemplates()
        self.loadConfig()

    def __repr__(self):
        return f"<Plugin {self._name} (uid={self._uid})>"

    @property
    def uid(self):
        return self._uid

    @property
    def name(self):
        """ Return the name of the plugin. """
        return self._name
    
    @property
    def uname(self):
        """ Return the unique name of the plugin. """
        return f"{self._uid}_{self._name}"

    @property
    def path(self):
        """ Return the absolute path of the plugin. """
        return self._path

    @property
    def isUserPlugin(self):
        """ Return whether the plugin is a user plugin (not maintained by the core Meshroom team). """
        return self._user

    @isUserPlugin.setter
    def isUserPlugin(self, user: bool):
        """ Set whether the plugin is a user plugin. """
        self._user = user

    @property
    def nodes(self):
        """
        Return the dictionary containing the NodeProvider objects associated to
        the plugin.
        """
        return self._nodeProviders

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

    @property
    def configFullEnv(self):
        """ Return the fusion of the os.environ dictionary with the configEnv dictionary. """
        return self._configFullEnv

    def addNodeProvider(self, nodeProvider: NodeProvider):
        """
        Add a node provider to the current plugin object and assign it as its containing plugin.
        The node provider is added to the dictionary of node providers with the name of the node
        descriptor as its key.

        Args:
            nodeProvider: the NodeProvider object to add to the Plugin.
        """
        self._nodeProviders[nodeProvider.nodeDescriptor.__name__] = nodeProvider
        nodeProvider.plugin = self

    def removeNodeProvider(self, name: str):
        """
        Remove a node provider from the current plugin object and delete any container relationship.

        Args:
            name: the name of the NodeProvider to remove.
        """
        if name in self._nodeProviders:
            self._nodeProviders[name].plugin = None
            del self._nodeProviders[name]
        else:
            logging.warning(f"node provider {name} is not part of the plugin {self.name}.")

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
                            logging.debug(f"{k}: {resolvedPath.as_posix()} does not exist "
                                          f"(path before resolution: {val}).")

                    self._configEnv[k] = str(val)

        except FileNotFoundError:
            logging.debug(f"No configuration file 'config.json' was found for {self.name}.")
        except json.JSONDecodeError as err:
            logging.error(f"Malformed JSON in the configuration file for {self.name}: {err}")
        except IOError as err:
            logging.error(f"Error while accessing the configuration file for {self.name}: {err}")

        # If both dictionaries have identical keys, os.environ overwrites existing values from _configEnv
        self._configFullEnv = self._configEnv | os.environ

    def containsNodeProvider(self, name: str) -> bool:
        """
        Return whether the node provider "name" is part of the plugin, independently from its
        status.

        Args:
            name: the name of the node provider to be checked.
        """
        return name in self._nodeProviders


class PluginManager(BaseObject):
    """
    Manager for all the loaded Plugin objects as well as the loaded NodeProvider objects.

    Members:
        plugins: dictionary containing all the loaded Plugins, with their name as the key
        nodeProviders: dictionary containing all the loaded NodeProviders 
    """

    def __init__(self):
        super().__init__()

        self._plugins: dict[str: Plugin] = {}  # loaded plugins
        self._nodeProviders: dict[str: NodeProvider] = {}  # loaded node providers

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

    def addPlugin(self, plugin: Plugin, loadNodeProviders: bool = True):
        """
        Load a Plugin object.

        Args:
            plugin: the Plugin to load and add to the list of loaded plugins.
            loadNodeProviders: True if all the NodeProviders from the plugin should be loaded
                                 at the same time the plugin is being loaded. Otherwise, the
                                 NodeProviders will have to be loaded at a later occasion.
        """
        pluginUName = plugin.uname
        if self.getPlugin(pluginUName):
            logging.warning(f"Plugin {pluginUName} is already loaded.")
            return
        self._plugins[pluginUName] = plugin
        if loadNodeProviders:
            for node in plugin.nodes:
                self.loadNodeProvider(plugin.nodes[node])

    def removePlugin(self, plugin: Plugin, unloadNodeProviders: bool = True):
        """
        Remove a loaded Plugin object.

        Args:
            plugin: the Plugin to remove from the list of loaded plugins.
            unloadNodeProviders: True if all the nodes from the plugin should be unloaded (if they
                                   are loaded) at the same time as the plugin is unloaded. Otherwise,
                                   the loaded NodeProviders will remain while the Plugin itself will
                                   be unloaded.
        """
        if self.getPlugin(plugin.uname):
            if unloadNodeProviders:
                for node in plugin.nodes.values():
                    self.unloadNodeProvider(node)
            del self._plugins[plugin.uname]

    def belongsToPlugin(self, name: str) -> Plugin:
        """
        Check whether the node provider belongs to a loaded plugin, independently from
        whether it has been loaded or not.

        Args:
            name: the name of the node provider that needs to be searched for across plugins.

        Returns:
            Plugin | None: the Plugin the node belongs to if it exists, None otherwise.
        """
        for plugin in self._plugins.values():
            if plugin.containsNodeProvider(name):
                return plugin
        return None

    def isLoaded(self, name: str) -> bool:
        """
        Return whether the node provider has been loaded already.

        Args:
            name: the name of the node provider.
        """
        return name in self._nodeProviders

    def getLoadedNodeProviders(self) -> dict[str: NodeProvider]:
        """
        Return a dictionary containing all the loaded NodeProviders, with
        {key, value} = {name, NodeProvider}.
        """
        return self._nodeProviders

    def getLoadedNodeProvider(self, name: str) -> NodeProvider:
        """
        Return the NodeProvider object that has been loaded under the name "name" if it exists.

        Args:
            name: the name of the NodeProvider.

        Returns:
            NodeProvider | None: the loaded NodeProvider object if it exists, None otherwise.
        """
        if self.isLoaded(name):
            return self._nodeProviders[name]
        return None

    def loadNodeProvider(self, nodeProvider: NodeProvider):
        """
        Load a node provider. A loaded node provider will become instantiable.
        If it is already loaded, or if there is an issue with the node description,
        the node provider will not be loaded and its status will be updated.

        Args:
            nodeProvider: the node provider to load.
        """
        name = nodeProvider.nodeDescriptor.__name__
        if self.isLoaded(name):
            existingPlugin: NodeProvider = self._nodeProviders[name]
            logging.warning(
                f"Could not load node {name} ({nodeProvider.path}) "
                f"because another node is already loaded with this name ({existingPlugin.path})"
            )
            return
        if nodeProvider.status in (NodeProviderStatus.DESC_ERROR,
                                 NodeProviderStatus.ERROR):
            logging.warning(
                f"Could not load node {name} ({nodeProvider.path}) "
                f"because the node is in error ({nodeProvider.status})."
            )
            return

        try:
            self._nodeProviders[name] = nodeProvider
            nodeProvider.status = NodeProviderStatus.LOADED
        except Exception as exc:
            logging.error(f"NodeProvider {name} could not be loaded: {exc}")
            nodeProvider.status = NodeProviderStatus.LOADING_ERROR

    def unloadNodeProvider(self, nodeProvider: NodeProvider):
        """
        Unload a node provider. When unloaded, a node provider cannot be instantiated anymore.
        If it is not loaded already, nothing happens.

        Args:
            nodeProvider: the node provider to unload.
        """
        name = nodeProvider.nodeDescriptor.__name__
        if self.isLoaded(name):
            if nodeProvider.status != NodeProviderStatus.LOADED:
                logging.warning(f"NodeProvider {name} is not correctly loaded.")
            else:
                nodeProvider.status = NodeProviderStatus.NOT_LOADED
            del self._nodeProviders[name]
