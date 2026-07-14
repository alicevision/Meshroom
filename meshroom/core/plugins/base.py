from __future__ import annotations

import importlib
import json
import logging
import os
import sys

from enum import Enum
from inspect import getfile
from pathlib import Path
from typing import Optional

from meshroom.common import BaseObject
from meshroom.core import desc
from meshroom.core.desc.attribute import ValueTypeErrors
from meshroom.core.submitter import BaseSubmitter
from meshroom.core.plugins.env import ProcessEnv
from meshroom.core.files import MESHROOM_PROJECT_EXTENSION, MESHROOM_TEMPLATE_EXTENSION, hasExtension, isTemplateFile


class PluginType(Enum):
    """
    Determines how a plugin is discovered and how its process environment is configured.
    """
    BUILTIN = 1  # Plugin folder using meshroom environment
    PATH = 2  # Plugin provided by a path
    REZ = 3  # Plugin provided by a rez package


class Plugin(BaseObject):
    """
    A collection of node plugins.

    Members:
        name: the name of the plugin (e.g. name of the Python module containing the node plugins)
        path: the absolute path of the plugin
        user: whether the plugin is a user plugin (not maintained by the core Meshroom team)
        nodeDescProviders: dictionary mapping the name of a node descriptor provider contained in the
                     plugin to its corresponding NodeDescProvider object
        submitterProviders: dictionary mapping the name of a submitter provider contained in the
                     plugin to its corresponding SubmitterProvider object
        templates: dictionary mapping the name of templates (.mgt files) associated to the plugin
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
        self._isUserPlugin: bool = False
        self._nodeDescProviders: dict[str: NodeDescProvider] = {}
        self._submitterProviders: dict[str: SubmitterProvider] = {}
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
        return self._isUserPlugin

    @isUserPlugin.setter
    def isUserPlugin(self, isUserPlugin: bool):
        """ Set whether the plugin is a user plugin. """
        self._isUserPlugin = isUserPlugin

    @property
    def nodeDescProviders(self):
        """
        Return the dictionary containing the NodeDescProvider objects associated to
        the plugin.
        """
        return self._nodeDescProviders

    @property
    def submitterProviders(self):
        """
        Return the dictionary containing the SubmitterProvider objects associated to
        the plugin.
        """
        return self._submitterProviders

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
        self._nodeDescProviders[nodeDescProvider.name] = nodeDescProvider
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

    def addSubmitterProvider(self, submitterClass: type[BaseSubmitter]):
        """
        Create a SubmitterProvider for "submitterClass" and add it to the current plugin object,
        assigning the plugin as its container. The submitter provider is added to the dictionary
        of submitter providers with the name of the submitter class as its key.

        Args:
            submitterClass: the BaseSubmitter subclass to create a SubmitterProvider for.
        """
        submitterProvider = SubmitterProvider(submitterClass, self)
        self._submitterProviders[submitterProvider.name] = submitterProvider

    def removeSubmitterProvider(self, name: str):
        """
        Remove a submitter provider from the current plugin object.

        Args:
            name: the name of the SubmitterProvider to remove.
        """
        if name in self._submitterProviders:
            del self._submitterProviders[name]
        else:
            logging.warning(f"submitter provider {name} is not part of the plugin {self.name}.")

    def containsSubmitterProvider(self, name: str) -> bool:
        """
        Return whether the submitter provider "name" is part of the plugin, independently from
        its status.

        Args:
            name: the name of the submitter provider to be checked.
        """
        return name in self._submitterProviders

    def loadTemplates(self):
        """
        Load all the pipeline templates that are available within the plugin folder.
        Whenever this method is called, the list of templates for the plugin is cleared,
        before being filled again.
        """
        self._templates.clear()
        for file in sorted(os.listdir(self.path)):
            filepath = os.path.join(self.path, file)
            templateName = Path(file).stem
            if hasExtension(filepath, (MESHROOM_TEMPLATE_EXTENSION,)):
                self._templates[templateName] = filepath
            elif hasExtension(filepath, (MESHROOM_PROJECT_EXTENSION,)) and isTemplateFile(filepath):
                self._templates.setdefault(templateName, filepath)

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
        # Python 3.9+ version: self._configFullEnv = self._configEnv | os.environ
        self._configFullEnv = {**self._configEnv, **os.environ}


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
        name: the name of the node descriptor, as declared by its class
        status: the loading status on the node descriptor provider
        errors: the list of errors (if there are any) when validating the description
                of the node or attempting to load it
        processEnv: the environment required for the node descriptor provider's process. It can either
                    be specific to this node descriptor provider, or be common for all the node
                    descriptor providers within the plugin
        timestamp: the timestamp corresponding to the last time the node description's file has been
                   modified
    """

    @staticmethod
    def __validateNodeDescClass(nodeDescClass: type[desc.BaseNode]) -> list[tuple[str, ValueTypeErrors]]:
        """
        Check that the node description class is a valid description. 
        To be valid, the default value of every parameter needs to correspond to the type
        of the parameter.
        An empty returned list means that every parameter is valid, and so is the node's description.
        If it is not valid, the returned list contains the names of the invalid parameters. In case
        of nested parameters (parameters in groups or lists, for example), the name of the parameter
        follows the name of the parent attributes. For example, if the attribute "x", contained in group
        "group", is invalid, then it will be added to the list as "group:x".

        Args:
            nodeDescClass: Description class of a node.

        Returns:
            errors: The list of invalid parameters if there are any, empty list otherwise.
        """
        errors = []
        for param in nodeDescClass.inputs:
            errMsg, errType = param.checkValueTypes()
            if errMsg:
                errors.append((errMsg, errType))
        for param in nodeDescClass.outputs:
            if param.value is None:
                if issubclass(nodeDescClass, desc.InitNode):
                    errors.append((f"{param.name}", ValueTypeErrors.DYNAMIC_OUTPUT))
                continue
            errMsg, errType = param.checkValueTypes()
            if errMsg:
                errors.append((errMsg, errType))
        return errors

    @staticmethod
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

    def __init__(self, nodeDescClass: type[desc.BaseNode], plugin: Plugin = None):
        super().__init__()
        self.path: str = Path(getfile(nodeDescClass)).resolve().as_posix()
        self.nodeDescClass: desc.BaseNode = nodeDescClass
        self.nodeDescClass.provider = self
        self.nodeDescClass.plugin = plugin
        self.plugin: Plugin = plugin

        self.status: NodeDescProviderStatus = NodeDescProviderStatus.NOT_LOADED
        self.errors: list[tuple[str, ValueTypeErrors]] = self.__validateNodeDescClass(nodeDescClass)

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
            logging.error(f"[Reload] {self.name}: The path at {self.path} was not "
                          f"not found.")
            return False

        if self._timestamp == timestamp:
            logging.info(f"[Reload] {self.name}: Not reloading. The node description "
                         f"at {self.path} has not been modified since the last load.")
            return False

        try:
            updated = importlib.reload(sys.modules.get(self.nodeDescClass.__module__))
        except Exception as exc:
            logging.error(f"[Reload] {self.name}: {exc} ({type(exc).__name__})")
            self.status = NodeDescProviderStatus.DESC_ERROR
            return False
        descriptor = getattr(updated, self.name)

        if not descriptor:
            self.status = NodeDescProviderStatus.ERROR
            logging.error(f"[Reload] {self.name}: The node description at {self.path} "
                          f"was not found.")
            return False

        self.errors = self.__validateNodeDescClass(descriptor)
        if self.errors:
            self.status = NodeDescProviderStatus.DESC_ERROR
            logging.error(f"[Reload] {self.name}: The node description at {self.path} "
                          f"has description errors.")
            return False

        self.nodeDescClass = descriptor
        self.nodeDescClass.provider = self
        self.nodeDescClass.plugin = self.plugin
        self._timestamp = timestamp
        self.status = NodeDescProviderStatus.NOT_LOADED
        logging.info(f"[Reload] {self.name}: Successful reloading.")
        return True

    @property
    def name(self) -> str:
        """ Return the name of the node descriptor, as declared by its class. """
        return self.nodeDescClass.__name__

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
        self.nodeDescClass.plugin = plugin

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


class SubmitterProviderStatus(Enum):
    """
    Validity status for SubmitterProvider objects.
    """
    VALID = 0  # The submitter was successfully instantiated
    ERROR = 1  # Error when instantiating the submitter


class SubmitterProvider(BaseObject):
    """
    Based on a BaseSubmitter subclass, a SubmitterProvider represents a loadable submitter.

    Members:
        plugin: the Plugin object that contains this submitter provider. Set once at
                construction and constant for the lifetime of the submitter provider.
        path: absolute path to the file containing the submitter's class
        submitterClass: the BaseSubmitter subclass
        name: the name of the submitter, as declared by its class
        status: the validity status of the submitter provider
        instance: the instantiated submitter, or None if instantiation failed
    """

    def __init__(self, submitterClass: type[BaseSubmitter], plugin: Plugin):
        super().__init__()
        self._plugin: Plugin = plugin
        self.path: str = Path(getfile(submitterClass)).resolve().as_posix()
        self.submitterClass: type[BaseSubmitter] = submitterClass
        self.status: SubmitterProviderStatus = SubmitterProviderStatus.VALID
        self.error: Optional[str] = None

        try:
            self.instance: Optional[BaseSubmitter] = submitterClass()
        except Exception as exc:
            self.error = f"SubmitterProvider {submitterClass.__name__} could not be instantiated: {exc}"
            self.instance = None
            self.status = SubmitterProviderStatus.ERROR

    @property
    def name(self) -> str:
        """ Return the name of the submitter, as declared by its class. """
        return self.submitterClass._name

    @property
    def plugin(self):
        """
        Return the Plugin object that contains this submitter provider. Set once at
        construction and constant for the lifetime of the submitter provider.
        """
        return self._plugin
