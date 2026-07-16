from __future__ import annotations

import importlib
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
from meshroom.core.files import MESHROOM_PROJECT_EXTENSION, MESHROOM_TEMPLATE_EXTENSION, hasExtension, isTemplateFile
from meshroom.core.plugins.config import PluginConfig
from meshroom.core.plugins.env import ProcessEnv, processEnvFactory


class PluginType(Enum):
    """
    Determines how a plugin is discovered and how its process environment is configured.
    """
    BUILTIN = 1  # Plugin folder using meshroom environment
    PATH = 2  # Plugin provided by a path
    REZ = 3  # Plugin provided by a rez package


class Plugin(BaseObject):
    """
    A centralized container that manages the plugin collection of NodeDescProvider objects and
    SubmitterProvider objects. Alongside plugin name, version, type, templates and configuration.

    Members:
        name: the name of the plugin (e.g. name of the Python module containing the node plugins)
        rootPath: the absolute path of the plugin's root folder
        path: the absolute path of the plugin's modules (its "meshroom" folder)
        version: the version of the plugin, or "unknown" if none was provided
        isUserPlugin: whether the plugin is a user plugin (not maintained by the core Meshroom team)
        type: the PluginType describing how the plugin was discovered and how its process
              environment is configured
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

    def __init__(self, name: str, rootPath: str, path: str, type: PluginType,
                 version: Optional[str] = None, isUserPlugin: bool = False,
                 config: Optional[PluginConfig] = None):
        super().__init__()

        self._name: str = name
        self._rootPath: str = rootPath
        self._path: str = path
        self._type: PluginType = type
        self._version: str = version
        self._isUserPlugin: bool = isUserPlugin
        self._nodeDescProviders: dict[str, NodeDescProvider] = {}
        self._submitterProviders: dict[str, SubmitterProvider] = {}
        self._templates: dict[str, str] = {}
        self._configEnv: dict[str, str] = {}

        # Get environment variables from config
        if config:
            self._configEnv = config.resolveEnv(self._path, self._name)
        # If both dictionaries have identical keys, os.environ overwrites existing values from _configEnv
        self._configFullEnv: dict[str, str] = self._configEnv | os.environ

        self.loadTemplates()

        envType = "rez" if type is PluginType.REZ else "dirtree"
        self._processEnv: ProcessEnv = processEnvFactory(self._rootPath, self._configEnv, self._name,
                                                          envType=envType)

    def __repr__(self):
        return f"<Plugin {self._name}>"

    @property
    def name(self):
        """ Return the name of the plugin. """
        return self._name

    @property
    def path(self):
        """ Return the absolute path of the plugin's modules (its "meshroom" folder). """
        return self._path

    @property
    def rootPath(self):
        """
        Return the absolute path of the plugin's root folder, containing python modules
        as well as any "bin"/"lib"/"lib64"/"venv" dependency folders.
        """
        return self._rootPath

    @property
    def type(self):
        """ Return the PluginType describing how the plugin was discovered. """
        return self._type

    @property
    def version(self):
        """ Return the version of the plugin, or "unknown" if none was provided. """
        if self._version and len(self._version) > 0:
            return self._version
        return "unknown"

    @property
    def isUserPlugin(self):
        """ Return whether the plugin is a user plugin (not maintained by the core Meshroom team). """
        return self._isUserPlugin

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

    def addNodeDescProvider(self, nodeDescClass: type[desc.BaseNode]) -> NodeDescProvider:
        """
        Create a NodeDescProvider for "nodeDescClass" and add it to the current plugin object,
        assigning the plugin as its container. The node descriptor provider is added to the dictionary
        of node descriptor providers with the name of the node descriptor as its key.

        Args:
            nodeDescClass: the desc.BaseNode subclass to create a NodeDescProvider for.

        Returns:
            NodeDescProvider: the created node descriptor provider.
        """
        nodeDescProvider = NodeDescProvider(nodeDescClass, self)
        self._nodeDescProviders[nodeDescProvider.name] = nodeDescProvider
        return nodeDescProvider

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

    def addSubmitterProvider(self, submitterClass: type[BaseSubmitter]) -> SubmitterProvider:
        """
        Create a SubmitterProvider for "submitterClass" and add it to the current plugin object,
        assigning the plugin as its container. The submitter provider is added to the dictionary
        of submitter providers with the name of the submitter class as its key.

        Args:
            submitterClass: the BaseSubmitter subclass to create a SubmitterProvider for.

        Returns:
            SubmitterProvider: the created submitter provider.
        """
        submitterProvider = SubmitterProvider(submitterClass, self)
        self._submitterProviders[submitterProvider.name] = submitterProvider
        return submitterProvider

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


class NodeDescProviderStatus(Enum):
    """
    Validity status for NodeDescProvider objects.
    """
    VALID = 0  # The node description is valid and can be instantiated
    DESC_ERROR = 1  # The node provider exists but has an invalid description
    ERROR = 2  # Error when importing the node provider from its module


class NodeDescProvider(BaseObject):
    """
    Based on a node description, a NodeDescProvider represents a loadable node.

    Members:
        plugin: the Plugin object that contains this node descriptor provider
        name: the name of the node descriptor, as declared by its class
        path: absolute path to the file containing the node's description
        nodeDescClass: the description of the node
        status: the loading status on the node descriptor provider
        error: a single formatted message combining every description "errors", or None if valid
        processEnv: the environment required for the node descriptor provider's process. It can either
                    be specific to this node descriptor provider, or be common for all the node
                    descriptor providers within the plugin
        runtimeEnv: the environment dictionary for the runtime, derived from processEnv
        commandPrefix: the command prefix for the node provider's execution, derived from processEnv
        commandSuffix: the command suffix for the node provider's execution, derived from processEnv
        configFullEnv: the plugin's full environment dictionary
        timestamp: the timestamp corresponding to the last time the node description's file has been
                   modified
    """

    @staticmethod
    def __validateNodeDescClass(nodeDescClass: type[desc.BaseNode]) -> Optional[str]:
        """
        Check that the node description class is a valid description. 
        To be valid, the default value of every parameter needs to correspond to the type
        of the parameter. In case of nested parameters (parameters in groups or lists, for example),
        the name of the parameter follows the name of the parent attributes. For example, if the attribute
        "x", contained in group "group", is invalid, then it will be added to the list as "group:x".

        Args:
            nodeDescClass: Description class of a node.

        Returns:
            error: The list of invalid parameters in a formatted error message.
        """
        errors: list[tuple[str, ValueTypeErrors]] = []
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
        errorMessages: list[str] = []
        for error in errors:
            errMsg, errType = error
            if errType == ValueTypeErrors.TYPE:
                errorMessages.append(f" - 'value': Invalid type for parameter '{errMsg}'.")
            elif errType == ValueTypeErrors.RANGE:
                errorMessages.append(f" - 'range': Invalid range value for parameter '{errMsg}'.")
            elif errType == ValueTypeErrors.DYNAMIC_OUTPUT:
                errorMessages.append(f" - 'value': Unsupported dynamic output for parameter '{errMsg}'.")
            else:
                errorMessages.append(f" - Unknown error for parameter '{errMsg}'.")
        if errorMessages:
            return f"NodeDescProvider {nodeDescClass.__name__} could not be validated:\n" + "\n".join(errorMessages)
        return None

    def __init__(self, nodeDescClass: type[desc.BaseNode], plugin: Plugin = None):
        super().__init__()
        self._plugin: Plugin = plugin
        self.path: str = Path(getfile(nodeDescClass)).resolve().as_posix()
        self.nodeDescClass: desc.BaseNode = nodeDescClass
        self.nodeDescClass.provider = self
        self.nodeDescClass.plugin = plugin
        self.nodeDescClass.packageName = plugin.name if plugin else ""

        self.status: NodeDescProviderStatus = NodeDescProviderStatus.VALID
        self.error: Optional[str] = self.__validateNodeDescClass(nodeDescClass)

        if self.error:
            self.status = NodeDescProviderStatus.DESC_ERROR

        self._processEnv = None
        if plugin:
            envType = "rez" if plugin.type is PluginType.REZ else "dirtree"
            self._processEnv: ProcessEnv = processEnvFactory(plugin.rootPath, plugin.configEnv, plugin.name,
                                                              pluginSubPackage=self.relativePackage, envType=envType)
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

        self.error = self.__validateNodeDescClass(descriptor)
        if self.error:
            self.status = NodeDescProviderStatus.DESC_ERROR
            logging.error(f"[Reload] {self.name}: The node description at {self.path} "
                          f"has description errors.")
            return False

        self.nodeDescClass = descriptor
        self.nodeDescClass.provider = self
        self.nodeDescClass.plugin = self.plugin
        self.nodeDescClass.packageName = self._plugin.name if self._plugin else ""
        self._timestamp = timestamp
        self.status = NodeDescProviderStatus.VALID
        logging.info(f"[Reload] {self.name}: Successful reloading.")
        return True

    @property
    def plugin(self):
        """
        Return the Plugin object that contains this node descriptor provider.
        If the node descriptor provider has not been assigned to a plugin yet, this value will
        be set to None.
        """
        return self._plugin

    @property
    def name(self) -> str:
        """ Return the name of the node descriptor, as declared by its class. """
        return self.nodeDescClass.__name__

    @property
    def absolutePackage(self) -> str:
        """
        Return the full dotted path of the package containing the node's description class.

        Only strip the last dotted component of the class' module name if that module is a leaf
        file within a package: if the class is declared directly in a package's "__init__.py",
        its module name already is that package's dotted path and must be kept as-is.
        """
        moduleName = self.nodeDescClass.__module__
        module = sys.modules.get(moduleName)
        if module is not None and hasattr(module, "__path__"):
            return moduleName
        return moduleName.rsplit(".", 1)[0]

    @property
    def relativePackage(self) -> str:
        """
        Return the dotted path of the package containing the node's description class,
        relative to the plugin's root (i.e. without the "_meshroomPlugins.<pluginName>" prefix).
        """
        return ".".join(self.absolutePackage.split(".")[2:])

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
    def configFullEnv(self) -> dict[str, str]:
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
        error: a single formatted message combining every submitter "errors", or None if valid
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
    def plugin(self):
        """
        Return the Plugin object that contains this submitter provider. Set once at
        construction and constant for the lifetime of the submitter provider.
        """
        return self._plugin

    @property
    def name(self) -> str:
        """ Return the name of the submitter, as declared by its class. """
        return self.submitterClass._name

    @property
    def absolutePackage(self) -> str:
        """
        Return the full dotted path of the package containing the submitter class.

        Only strip the last dotted component of the class' module name if that module is a leaf
        file within a package: if the class is declared directly in a package's "__init__.py",
        its module name already is that package's dotted path and must be kept as-is.
        """
        moduleName = self.submitterClass.__module__
        module = sys.modules.get(moduleName)
        if module is not None and hasattr(module, "__path__"):
            return moduleName
        return moduleName.rsplit(".", 1)[0]

    @property
    def relativePackage(self) -> str:
        """
        Return the dotted path of the package containing the submitter class,
        relative to the plugin's root (i.e. without the "_meshroomPlugins.<pluginName>" prefix).
        """
        return ".".join(self.absolutePackage.split(".")[2:])