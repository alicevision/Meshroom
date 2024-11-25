""" Node plugins.
"""
# Types
from typing import Dict, List
from types import ModuleType

# STD
import importlib
import logging
import os
import pkgutil
import sys

# Internal
from meshroom.core import desc

# Plugins
from .base import Status, Pluginator


class NodeDescriptor(object):
    """ Class to describe a Node Plugin.
    """

    _DEFAULT_VERSION = "0"

    def __init__(self, name: str, descriptor: desc.Node) -> None:
        """ Constructor.

        Args:
            name (str): Name of the Node.
            descriptor (desc.Node): The Node descriptor.
        """
        super().__init__()

        # Node descriptions
        self._name: str = name
        self._descriptor: desc.Node = descriptor

        # Update the Node Descriptor's plugin
        self._descriptor.plugin: NodeDescriptor = self

        # Module descriptions
        self._module: ModuleType = sys.modules.get(self._descriptor.__module__)
        self._version: str = getattr(self._module, "__version__", self._DEFAULT_VERSION)
        self._path: str = self._module.__file__

        # When the plugin was last modified ?
        self._mtime: float = os.path.getmtime(self._path)

        self._errors: List[str] = self._validate()

    # Properties
    name = property(lambda self: self._name)
    descriptor = property(lambda self: self._descriptor)
    category = property(lambda self: self._descriptor.category)
    errors = property(lambda self: self._errors)
    documentation = property(lambda self: self._descriptor.documentation)
    version = property(lambda self: self._version)
    path = property(lambda self: self._path)

    @property
    def status(self) -> Status:
        """ Returns the status of the plugin.
        """
        # If no errors -> then it is loaded and available
        return Status(not self._errors)

    def __repr__(self):
        """ Represents the Instance.
        """
        return f"NodeDescriptor::{self._name} at {hex(id(self))}"

    def _validate(self) -> List[str]:
        """ Check that the node has a valid description before being loaded. For the description to be valid, the
        default value of every parameter needs to correspond to the type of the parameter.

        An empty returned list means that every parameter is valid, and so is the node's description. If it is not
        valid, the returned list contains the names of the invalid parameters. In case of nested parameters (parameters
        in groups or lists, for example), the name of the parameter follows the name of the parent attributes.

        For example,
        If the attribute "x", contained in group "group", is invalid, then it will be added to the list as "group:x".

        Returns:
            errors (list<str>): the list of invalid parameters if there are any, empty list otherwise.
        """
        errors = []

        for param in self._descriptor.inputs:
            err = param.checkValueTypes()
            if err:
                errors.append(err)

        for param in self._descriptor.outputs:
            # Ignore the output attributes with None as the value
            if param.value is None:
                continue

            err = param.checkValueTypes()
            if err:
                errors.append(err)

        # Return any errors while validating the input and output attributes
        return errors

    # Public
    def modified(self) -> bool:
        """ Returns True if the plugin module has been modified after it was loaded.
        """
        # A Module is modified if the modification time of the file is greater than the modification time
        # of the file when it was last loaded in the Descriptor
        return os.path.getmtime(self._path) > self._mtime

    def reload(self, force: bool=False) -> bool:
        """ Reloads the Node. Defaults to only loading the plugin if it has been modified.
        Use force=True to load the plugin what so ever.

        Args:
            force (bool): Set to True to force load the Node Plugin.

        Returns:
            bool. True when the plugin was reloaded successfully, else False.
        """
        # If the plugin's source is not modified and there is no force operation to reload
        # ignore reloading the plugin, as it could end up changing the graph topology if the plugin
        # has been instanced in the graph
        if not force and not self.modified():
            return False

        # Reload the Module
        updated = importlib.reload(self._module)

        # Get the Descriptor
        descriptor = getattr(updated, self._name)

        # Cannot find the current class on the updated module ?
        if not descriptor:
            return

        # Update the descriptor and call for validation
        self._module = updated

        self._descriptor = descriptor
        self._descriptor.plugin = self

        # Update the errors if any that may have been introduced
        self._errors = self._validate()

        # Update the version as it may have updated with the update
        self._version = getattr(self._module, "__version__", self._DEFAULT_VERSION)

        # Update the Modifcation time of the descriptor
        self._mtime = os.path.getmtime(self._path)

        return True


class NodePluginManager(object):
    """ A Singleton class Managing the Node plugins for Meshroom.
    """
    # Static class instance to ensure we have only one created at all times
    _instance = None

    # The core class to which the Node plugins belong
    _CLASS_TYPE = desc.Node

    def __new__(cls):
        # Verify that the instance we have is of the current type
        if not isinstance(cls._instance, cls):
            # Create an instance to work with
            cls._instance = object.__new__(cls)

            # Init the class parameters
            # The class parameters need to be initialised outside __init__ as when Cls() gets invoked __init__ gets
            # called as well, so even when we get the same instance back, the params are updated for this and every
            # other instance and that what will affect attrs in all places where the current instance is being used
            cls._instance.init()

        # Return the instantiated instance
        return cls._instance

    def init(self) -> None:
        """ Constructor for members.
        """
        self._descriptors: Dict[str: NodeDescriptor] = {}     # pylint: disable=attribute-defined-outside-init

    # Properties
    descriptors = property(lambda self: self._descriptors)

    # Public
    def registered(self, name: str) -> bool:
        """ Returns whether the plugin has been registered already or not.

        Args:
            name (str): Name of the plugin.

        Returns:
            bool. True if the plugin was registered, else False.
        """
        return name in self._descriptors

    def status(self, name: str) -> Status:
        """ Returns the current status of the plugin.

        Args:
            name (str): Name of the plugin.

        Returns:
            Status. The current status of the plugin.
        """
        # Fetch the plugin Descriptor
        plugin = self._descriptors.get(name)

        if not plugin:
            return Status.UNLOADED

        # Return the status from the plugin itself
        return plugin.status

    def errors(self, name) -> List[str]:
        """ Returns the Errors on the plugins if there are any.

        Args:
            name (str): Name of the plugin.

        Returns:
            list<str>. the list of invalid parameters if there are any, empty list otherwise.
        """
        # Fetch the plugin Descriptor
        plugin = self._descriptors.get(name)

        if not plugin:
            return []

        # Return any errors from the plugin side
        return plugin.errors

    def registerNode(self, descriptor: desc.Node) -> bool:
        """ Registers a Node into Meshroom.

        Args:
            descriptor (desc.Node): The Node descriptor.

        Returns:
            bool. Returns True if the node is registered. False if it is already registered.
        """
        # Plugin name
        name = descriptor.__name__

        # Already registered ?
        if self.registered(name):
            return False

        # Register it
        self.register(name, descriptor)

        return True

    def unregisterNode(self, descriptor: desc.Node) -> None:
        """ Unregisters the Node from the Registered Set of Nodes.

        Args:
            descriptor (desc.Node): The Node descriptor.
        """
        # Plugin name
        name = descriptor.__name__

        # Ensure that we have this node already present
        assert name in self._descriptors
        # Delete the instance
        del self._descriptors[name]

    def register(self, name: str, descriptor: desc.Node) -> None:
        """ Registers a Node within meshroom.

        Args:
            name (str): Name of the Node Plugin.
            descriptor (desc.Node): The Node descriptor.
        """
        self._descriptors[name] = NodeDescriptor(name, descriptor)

    def descriptor(self, name: str) -> desc.Node:
        """ Returns the Node Desc for the provided name.

        Args:
            name (str): Name of the plugin.

        Returns:
            desc.Node. The Node Desc instance.
        """
        # Returns the plugin for the provided name
        plugin = self._descriptors.get(name)

        # Plugin not found with the name
        if not plugin:
            return None

        # Return the Node Descriptor for the plugin
        return plugin.descriptor

    def load(self, directory) -> None:
        """ Loads Node from the provided directory.
        """
        for _, package, ispkg in pkgutil.walk_packages([directory]):
            if not ispkg:
                continue

            # Get the plugins from the provided directory and the python package
            descriptors = Pluginator.get(directory, package, self._CLASS_TYPE)

            for descriptor in descriptors:
                self.registerNode(descriptor)

            logging.debug('Nodes loaded [{}]: {}'.format(package, ', '.join([d.__name__ for d in descriptors])))
