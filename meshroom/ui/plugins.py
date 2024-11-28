""" UI Component for the Plugin System.
"""
# Qt
from PySide6.QtCore import Slot, QObject, Property, Signal

# Internal
from meshroom.core import pluginManager
from meshroom.common import BaseObject, DictModel


class Plugin(BaseObject):
    """ Representation of a Plugin in UI.
    """

    def __init__(self, descriptor):
        """ Constructor.

        Args:
            descriptor (NodeDescriptor): A Plugin descriptor.
        """
        super().__init__()

        self._descriptor = descriptor

        # Any Node errors
        self._nodeErrors = self._errors()

    def _errors(self) -> str:
        """ Returns the Error Description for the Node Plugin if there are any.
        """
        if not self._descriptor.errors:
            return ""

        errors = ["Following parameters have invalid default values/ranges:"]

        # Add the parameters from the node Errors
        errors.extend([f"* Param {param}" for param in self._descriptor.errors])

        return "\n".join(errors)

    @Slot(result=bool)
    def reload(self) -> bool:
        """ Reloads the plugin descriptor.

        Returns:
            bool. The reload status.
        """
        # The plugin descriptor reloads only if the file was modified after it was last loaded
        if not self._descriptor.reload():
            return False

        # Update the Node errors
        self._nodeErrors = self._errors()

        # Plugin was modified
        return True

    name = Property(str, lambda self: self._descriptor.name, constant=True)
    documentation = Property(str, lambda self: self._descriptor.documentation, constant=True)
    loaded = Property(bool, lambda self: bool(self._descriptor.status), constant=True)
    version = Property(str, lambda self: self._descriptor.version, constant=True)
    path = Property(str, lambda self: self._descriptor.path, constant=True)
    errors = Property(str, lambda self: self._nodeErrors, constant=True)
    category = Property(str, lambda self: self._descriptor.category, constant=True)


class NodesPluginManager(QObject):
    """ UI Plugin Manager Component. Serves as a Bridge between the core Nodes' Plugin Manager and how the
    users interact with it.
    """

    def __init__(self, parent=None):
        """ Constructor.

        Keyword Args:
            parent (QObject): The Parent for the Plugin Manager.
        """
        super().__init__(parent=parent)

        # The core Plugin Manager
        self._manager = pluginManager

        # The plugins as a Model which can be communicated to the frontend
        self._plugins = DictModel(keyAttrName='name', parent=self)

        # Reset the plugins model
        self._reset()

    # Signals
    pluginsChanged = Signal()

    # Properties
    plugins = Property(BaseObject, lambda self: self._plugins, notify=pluginsChanged)

    # Protected
    def _reset(self):
        """ Requeries and Resets the Plugins Model from the core Plugin Manager for UI refreshes.
        """
        plugins = [Plugin(desc) for desc in self._manager.descriptors.values()]

        # Reset the plugins model
        self._plugins.reset(plugins)

    # Public
    @Slot(str)
    def load(self, directory):
        """ Load plugins from a given directory, which serves as a package of Meshroom Node Modules.

        Args:
            directory (str): Path to the plugin package to import.
        """
        # Load the plugin(s) from the provided directory package
        self._manager.load(directory)

        # Reset the plugins model
        self._reset()

        # Emit that the plugins have now been updated
        self.pluginsChanged.emit()
