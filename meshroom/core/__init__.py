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
        logging.warning('== The following plugins could not be loaded ==\n'
                        '{}\n'
                        .format('\n'.join(errors)))
    return pluginTypes


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
            print('Plugins loaded: ', ', '.join([nodeType.__name__ for nodeType in nodeTypes]))


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
subs = loadSubmitters(meshroomFolder, 'submitters')
# -  additional 3rd party submitters
if "MESHROOM_SUBMITTERS_PATH" in os.environ:
    subs += loadSubmitters(os.environ["MESHROOM_SUBMITTERS_PATH"], 'submitters')

for sub in subs:
    registerSubmitter(sub())
