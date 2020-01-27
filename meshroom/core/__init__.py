from __future__ import print_function

import hashlib
from contextlib import contextmanager
import importlib
import inspect
import os
import re
import tempfile
import uuid
import logging
import pkgutil

import sys

try:
    # for cx_freeze
    import encodings.ascii
    import encodings.idna
    import encodings.utf_8
except:
    pass

from meshroom.core.submitter import BaseSubmitter
from . import desc

# Setup logging
logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.INFO)

# make a UUID based on the host ID and current time
sessionUid = str(uuid.uuid1())

cacheFolderName = 'MeshroomCache'
defaultCacheFolder = os.environ.get('MESHROOM_CACHE', os.path.join(tempfile.gettempdir(), cacheFolderName))
nodesDesc = {}
submitters = {}


def hashValue(value):
    """ Hash 'value' using sha1. """
    hashObject = hashlib.sha1(str(value).encode('utf-8'))
    return hashObject.hexdigest()


@contextmanager
def add_to_path(p):
    import sys
    old_path = sys.path
    sys.path = sys.path[:]
    sys.path.insert(0, p)
    try:
        yield
    finally:
        sys.path = old_path


def loadPlugins(folder, packageName, classType):
    """
    """

    pluginTypes = []
    errors = []

    # temporarily add folder to python path
    with add_to_path(folder):
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
                for p in plugins:
                    p.packageName = packageName
                    p.packageVersion = packageVersion
                pluginTypes.extend(plugins)
            except Exception as e:
                errors.append('  * {}: {}'.format(pluginName, str(e)))

    if errors:
        logging.warning('== The following "{package}" plugins could not be loaded ==\n'
                        '{errorMsg}\n'
                        .format(package=packageName, errorMsg='\n'.join(errors)))
    return pluginTypes


class Version(object):
    """
    Version provides convenient properties and methods to manipulate and compare version names.
    """
    def __init__(self, versionName):
        """
        Args:
            versionName (str): the name of the version as a string
        """
        self.name = versionName
        self.components = Version.toComponents(self.name)

    def __repr__(self):
        return self.name

    def __neg__(self):
        return not self.name

    def __len__(self):
        return len(self.components)

    def __eq__(self, other):
        """
        Test equality between 'self' with 'other'.

        Args:
            other (Version): the version to compare to

        Returns:
            bool: whether the versions are equal
        """
        return self.name == other.name

    def __lt__(self, other):
        """
        Test 'self' inferiority to 'other'.

        Args:
            other (Version): the version to compare to

        Returns:
            bool: whether self is inferior to other
        """
        # sequence comparison works natively for this use-case
        return self.name < other.name

    def __le__(self, other):
        """
        Test 'self' inferiority or equality to 'other'.

        Args:
            other (Version): the version to compare to

        Returns:
            bool: whether self is inferior or equal to other
        """
        return self.name <= other.name

    @staticmethod
    def toComponents(versionName):
        """
        Split 'versionName' as a tuple of individual components.

        Args:
            versionName (str): version name

        Returns:
            tuple of str: split version numbers
        """
        if not versionName:
            return ()
        return tuple(versionName.split("."))

    @property
    def major(self):
        """ Version major number. """
        return self.components[0]

    @property
    def minor(self):
        """ Version minor number. """
        if len(self) < 2:
            return ""
        return self.components[1]

    @property
    def micro(self):
        """ Version micro number. """
        if len(self) < 3:
            return ""
        return self.components[2]


def moduleVersion(moduleName, default=None):
    """ Return the version of a module indicated with '__version__' keyword.

    Args:
        moduleName (str): the name of the module to get the version of
        default: the value to return if no version info is available

    Returns:
        str: the version of the module
    """
    return getattr(sys.modules[moduleName], "__version__", default)


def nodeVersion(nodeDesc, default=None):
    """ Return node type version for the given node description class.

    Args:
        nodeDesc (desc.Node): the node description class
        default: the value to return if no version info is available

    Returns:
        str: the version of the node type
    """
    return moduleVersion(nodeDesc.__module__, default)


def registerNodeType(nodeType):
    """ Register a Node Type based on a Node Description class.

    After registration, nodes of this type can be instantiated in a Graph.
    """
    global nodesDesc
    if nodeType.__name__ in nodesDesc:
        raise RuntimeError("Node Desc {} is already registered.".format(nodeType.__name__))
    nodesDesc[nodeType.__name__] = nodeType


def unregisterNodeType(nodeType):
    """ Remove 'nodeType' from the list of register node types. """
    global nodesDesc
    assert nodeType.__name__ in nodesDesc
    del nodesDesc[nodeType.__name__]


def loadNodes(folder, packageName):
    return loadPlugins(folder, packageName, desc.Node)


def loadAllNodes(folder):
    global nodesDesc
    for importer, package, ispkg in pkgutil.walk_packages([folder]):
        if ispkg:
            nodeTypes = loadNodes(folder, package)
            for nodeType in nodeTypes:
                registerNodeType(nodeType)
            logging.debug('Plugins loaded: ', ', '.join([nodeType.__name__ for nodeType in nodeTypes]))


def registerSubmitter(s):
    global submitters
    if s.name in submitters:
        raise RuntimeError("Submitter {} is already registered.".format(s.name))
    submitters[s.name] = s


def loadSubmitters(folder, packageName):
    return loadPlugins(folder, packageName, BaseSubmitter)


meshroomFolder = os.path.dirname(os.path.dirname(__file__))

# Load plugins:
# - Nodes
loadAllNodes(folder=os.path.join(meshroomFolder, 'nodes'))
# - Submitters
subs = loadSubmitters(os.environ.get("MESHROOM_SUBMITTERS_PATH", meshroomFolder), 'submitters')

for sub in subs:
    registerSubmitter(sub())
