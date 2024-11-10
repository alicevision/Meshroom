""" Base functionality for Plugins.
"""
# Types
from typing import List

# STD
from contextlib import contextmanager
import enum
import importlib
import inspect
import logging
import pkgutil


class Status(enum.IntEnum):
    """ Enum describing the state of the plugin.
    """

    # UNLOADED or NOT Available - Describing that the plugin is not available in the current set of plugins
    UNLOADED = -1

    # ERRORED describes that the plugin exists but could not be loaded due to errors with the structure
    ERRORED = 0

    # LOADED describes that the plugin is currently loaded and is fully functional
    LOADED = 1


class Pluginator:
    """ The common plugin utilities.
    """

    @staticmethod
    @contextmanager
    def add_to_path(_p):
        """ A Context Manager to add the provided path to Python's sys.path temporarily.
        """
        import sys                  # pylint: disable=import-outside-toplevel
        old_path = sys.path
        sys.path = sys.path[:]
        sys.path.insert(0, _p)
        try:
            yield
        finally:
            sys.path = old_path

    @staticmethod
    def get(folder, packageName, classType) -> List:
        """ Returns Array of Plugin, each holding the plugin and the module it belongs to.

        Args:
            folder (str): Path to the Directory.
            packageName (str): Name of the package to import.
            classType (desc.Node | BaseSubmitter): The base type of plugin which is being imported.
        """
        pluginTypes = []
        errors = []

        # temporarily add folder to python path
        with Pluginator.add_to_path(folder):
            # import node package
            package = importlib.import_module(packageName)
            packageName = package.packageName if hasattr(package, 'packageName') else package.__name__
            packageVersion = getattr(package, "__version__", None)

            for importer, pluginName, ispkg in pkgutil.iter_modules(package.__path__):
                pluginModuleName = '.' + pluginName

                try:
                    pluginMod = importlib.import_module(pluginModuleName, package=package.__name__)
                    plugins = [plugin for name, plugin in inspect.getmembers(pluginMod, inspect.isclass)
                            if plugin.__module__ == '{}.{}'.format(package.__name__, pluginName)
                            and issubclass(plugin, classType)]
                    if not plugins:
                        logging.warning("No class defined in plugin: {}".format(pluginModuleName))

                    # Update the package name and version on the plugin
                    for p in plugins:
                        p.packageName = packageName
                        p.packageVersion = packageVersion

                    # Extend all of the plugins
                    pluginTypes.extend(plugins)
                except Exception as exc:
                    errors.append('  * {}: {}'.format(pluginName, str(exc)))

        if errors:
            logging.warning('== The following "{package}" plugins could not be loaded ==\n'
                            '{errorMsg}\n'
                            .format(package=packageName, errorMsg='\n'.join(errors)))

        return pluginTypes
