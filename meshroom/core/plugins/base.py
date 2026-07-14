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


class Plugin(BaseObject):
    """
    A collection of node plugins.

    Members:
        name: the name of the plugin (e.g. name of the Python module containing the node plugins)
        path: the absolute path of the plugin
        user: whether the plugin is a user plugin (not maintained by the core Meshroom team)
        nodeDescProviders: dictionary mapping the name of a node descriptor provider contained in the
                     plugin to its corresponding NodeDescProvider object
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

        self._nodeDescProviders: dict[str: NodeDescProvider] = {}
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
        Return the dictionary containing the NodeDescProvider objects associated to
        the plugin.
        """
        return self._nodeDescProviders

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

    def addNodeDescProvider(self, nodeDescProvider: NodeDescProvider):
        """
        Add a node descriptor provider to the current plugin object and assign it as its containing
        plugin. The node descriptor provider is added to the dictionary of node descriptor providers
        with the name of the node descriptor as its key.

        Args:
            nodeDescProvider: the NodeDescProvider object to add to the Plugin.
        """
        self._nodeDescProviders[nodeDescProvider.nodeDescClass.__name__] = nodeDescProvider
        nodeDescProvider.plugin = self

    def removeNodeDescProvider(self, name: str):
        """
        Remove a node descriptor provider from the current plugin object and delete any container
        relationship.

        Args:
            name: the name of the NodeDescProvider to remove.
        """
        if name in self._nodeDescProviders:
            self._nodeDescProviders[name].plugin = None
            del self._nodeDescProviders[name]
        else:
            logging.warning(f"Node descriptor provider {name} is not part of the plugin {self.name}.")

    def containsNodeDescProvider(self, name: str) -> bool:
        """
        Return whether the node descriptor provider "name" is part of the plugin, independently
        from its status.

        Args:
            name: the name of the node descriptor provider to be checked.
        """
        return name in self._nodeDescProviders
    
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


class NodeDescProviderStatus(Enum):
    """
    Loading status for NodeDescProvider objects.
    """
    NOT_LOADED = 0  # The node descriptor provider exists but is not loaded and cannot be used (not registered)
    LOADED = 1  # The node descriptor provider is currently loaded and functional (it has been registered)
    DESC_ERROR = 2  # The node descriptor provider exists but has an invalid description
    LOADING_ERROR = 3  # The node descriptor provider exists and is valid but could not be successfully registered
    ERROR = 4  # Error when importing the node descriptor provider from its module


class NodeDescProvider(BaseObject):
    """
    Based on a node description, a NodeDescProvider represents a loadable node.

    Members:
        plugin: the Plugin object that contains this node descriptor provider
        path: absolute path to the file containing the node's description
        nodeDescClass: the description of the node
        status: the loading status on the node descriptor provider
        errors: the list of errors (if there are any) when validating the description
                of the node or attempting to load it
        processEnv: the environment required for the node descriptor provider's process. It can either
                    be specific to this node descriptor provider, or be common for all the node
                    descriptor providers within the plugin
        timestamp: the timestamp corresponding to the last time the node description's file has been
                   modified
    """

    def __init__(self, nodeDesc: desc.BaseNode, plugin: Plugin = None):
        super().__init__()
        self.plugin: Plugin = plugin
        self.path: str = Path(getfile(nodeDesc)).resolve().as_posix()
        self.nodeDescClass: desc.BaseNode = nodeDesc
        self.nodeDescClass.provider = self

        self.status: NodeDescProviderStatus = NodeDescProviderStatus.NOT_LOADED
        self.errors: list[tuple[str, ValueTypeErrors]] = validateNodeDesc(nodeDesc)

        if self.errors:
            self.status = NodeDescProviderStatus.DESC_ERROR

        self._processEnv = None
        self._timestamp = os.path.getmtime(self.path)

    def reload(self) -> bool:
        """
        Reload the node descriptor provider and update its status accordingly. If the timestamp of the
        node descriptor provider's path has not changed since the last time the plugin has been loaded,
        then nothing will happen.

        Returns:
            bool: True if the node descriptor provider has successfully been reloaded (i.e. there was
                  no error, and some changes were made since its last loading), False otherwise.
        """
        timestamp = 0.0
        try:
            timestamp = os.path.getmtime(self.path)
        except FileNotFoundError:
            self.status = NodeDescProviderStatus.ERROR
            logging.error(f"[Reload] {self.nodeDescClass.__name__}: The path at {self.path} was not "
                          f"not found.")
            return False

        if self._timestamp == timestamp:
            logging.info(f"[Reload] {self.nodeDescClass.__name__}: Not reloading. The node description "
                         f"at {self.path} has not been modified since the last load.")
            return False

        try:
            updated = importlib.reload(sys.modules.get(self.nodeDescClass.__module__))
        except Exception as exc:
            logging.error(f"[Reload] {self.nodeDescClass.__name__}: {exc} ({type(exc).__name__})")
            self.status = NodeDescProviderStatus.DESC_ERROR
            return False
        descriptor = getattr(updated, self.nodeDescClass.__name__)

        if not descriptor:
            self.status = NodeDescProviderStatus.ERROR
            logging.error(f"[Reload] {self.nodeDescClass.__name__}: The node description at {self.path} "
                          f"was not found.")
            return False

        self.errors = validateNodeDesc(descriptor)
        if self.errors:
            self.status = NodeDescProviderStatus.DESC_ERROR
            logging.error(f"[Reload] {self.nodeDescClass.__name__}: The node description at {self.path} "
                          f"has description errors.")
            return False

        self.nodeDescClass = descriptor
        self.nodeDescClass.provider = self
        self._timestamp = timestamp
        self.status = NodeDescProviderStatus.NOT_LOADED
        logging.info(f"[Reload] {self.nodeDescClass.__name__}: Successful reloading.")
        return True

    @property
    def plugin(self):
        """
        Return the Plugin object that contains this node descriptor provider.
        If the node descriptor provider has not been assigned to a plugin yet, this value will
        be set to None.
        """
        return self._plugin

    @plugin.setter
    def plugin(self, plugin: Plugin):
        """ Assign this node descriptor provider to a containing Plugin object. """
        self._plugin = plugin

    @property
    def isUserPlugin(self):
        """ Return whether the node descriptor provider belongs to a user plugin. """
        if self.plugin:
            return self.plugin.isUserPlugin
        return False

    @property
    def processEnv(self):
        """"
        Return the process environment that is specific to the node descriptor provider if it has any.
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
        """ Return the command prefix for the NodeDescProvider's execution. """
        if not self.processEnv:
            return ""
        return self.processEnv.getCommandPrefix()

    @property
    def commandSuffix(self) -> str:
        """ Return the command suffix for the NodeDescProvider's execution. """
        if not self.processEnv:
            return ""
        return self.processEnv.getCommandSuffix()

    @property
    def configFullEnv(self) -> dict[str: str]:
        """ Return the plugin's full environment dictionary. """
        if not self.plugin:
            return {}
        return self.plugin.configFullEnv
