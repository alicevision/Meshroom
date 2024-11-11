import hashlib
import os
import tempfile
import uuid
import logging

import sys

try:
    # for cx_freeze
    import encodings.ascii
    import encodings.idna
    import encodings.utf_8
except Exception:
    pass

from meshroom.core.submitter import BaseSubmitter
from meshroom import _plugins

# Setup logging
logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.INFO)

# make a UUID based on the host ID and current time
sessionUid = str(uuid.uuid1())

cacheFolderName = 'MeshroomCache'
defaultCacheFolder = os.environ.get('MESHROOM_CACHE', os.path.join(tempfile.gettempdir(), cacheFolderName))
submitters = {}
pipelineTemplates = {}

# Manages plugins for Meshroom Nodes
pluginManager = _plugins.NodePluginManager()

# Plugin States
PluginStatus = _plugins.Status


def hashValue(value):
    """ Hash 'value' using sha1. """
    hashObject = hashlib.sha1(str(value).encode('utf-8'))
    return hashObject.hexdigest()


class Version(object):
    """
    Version provides convenient properties and methods to manipulate and compare versions.
    """

    def __init__(self, *args):
        """
        Args:
            *args (convertible to int): version values
        """
        if len(args) == 0:
            self.components = tuple()
            self.status = str()
        elif len(args) == 1:
            versionName = args[0]
            if not versionName: # If this was initialised with Version(None) or Version("")
                self.components = tuple()
                self.status = str()
            elif isinstance(versionName, str):
                self.components, self.status = Version.toComponents(versionName)
            elif isinstance(versionName, (list, tuple)):
                self.components = tuple([int(v) for v in versionName])
                self.status = str()
            else:
                raise RuntimeError("Version: Unsupported input type.")
        else:
            self.components = tuple([int(v) for v in args])
            self.status = str()

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
        return self.components < other.components

    def __le__(self, other):
        """
        Test 'self' inferiority or equality to 'other'.

        Args:
            other (Version): the version to compare to

        Returns:
            bool: whether self is inferior or equal to other
        """
        return self.components <= other.components

    @staticmethod
    def toComponents(versionName):
        """
        Split 'versionName' as a tuple of individual components, including its status if
        there is any.

        Args:
            versionName (str): version name

        Returns:
            tuple of int, string: split version numbers, status if any (or empty string)
        """
        if not versionName:
            return (), str()

        status = str()
        # If there is a status, it is placed after a "-"
        splitComponents = versionName.split("-", maxsplit=1)
        if (len(splitComponents) > 1):  # If there is no status, splitComponents is equal to [versionName]
            status = splitComponents[-1]
        return tuple([int(v) for v in splitComponents[0].split(".")]), status

    @property
    def name(self):
        """ Version major number. """
        return ".".join([str(v) for v in self.components])

    @property
    def major(self):
        """ Version major number. """
        return self.components[0]

    @property
    def minor(self):
        """ Version minor number. """
        if len(self) < 2:
            return 0
        return self.components[1]

    @property
    def micro(self):
        """ Version micro number. """
        if len(self) < 3:
            return 0
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
    # Register the node in plugin manager
    registered = pluginManager.registerNode(nodeType)

    # The plugin was already registered
    if not registered:
        return

    # Plugin Name
    name = nodeType.__name__

    # Check the status of the plugin to identify if we have any errors on it while loading ?
    if pluginManager.status(name) == PluginStatus.ERRORED:
        errors = ", ".join(pluginManager.errors(name))
        logging.warning(f"[PluginManager] {name}: The following parameters do not have valid default values/ranges: {errors}.")


def unregisterNodeType(nodeType):
    """ Remove 'nodeType' from the list of register node types. """
    # Unregister the node from plugin manager
    pluginManager.unregisterNode(nodeType)


def loadAllNodes(folder):
    # Load plugins from the node's plugin manager
    pluginManager.load(folder)


def registerSubmitter(s):
    global submitters
    if s.name in submitters:
        logging.error("Submitter {} is already registered.".format(s.name))
    submitters[s.name] = s


def loadSubmitters(folder, packageName):
    return _plugins.Pluginator.get(folder, packageName, BaseSubmitter)


def loadPipelineTemplates(folder):
    global pipelineTemplates
    for file in os.listdir(folder):
        if file.endswith(".mg") and file not in pipelineTemplates:
            pipelineTemplates[os.path.splitext(file)[0]] = os.path.join(folder, file)


def initNodes():
    meshroomFolder = os.path.dirname(os.path.dirname(__file__))
    additionalNodesPath = os.environ.get("MESHROOM_NODES_PATH", "").split(os.pathsep)
    # filter empty strings
    additionalNodesPath = [i for i in additionalNodesPath if i]
    nodesFolders = [os.path.join(meshroomFolder, 'nodes')] + additionalNodesPath
    for f in nodesFolders:
        loadAllNodes(folder=f)


def initSubmitters():
    meshroomFolder = os.path.dirname(os.path.dirname(__file__))
    subs = loadSubmitters(os.environ.get("MESHROOM_SUBMITTERS_PATH", meshroomFolder), 'submitters')
    for sub in subs:
        registerSubmitter(sub())


def initPipelines():
    meshroomFolder = os.path.dirname(os.path.dirname(__file__))
    # Load pipeline templates: check in the default folder and any folder the user might have
    # added to the environment variable
    additionalPipelinesPath = os.environ.get("MESHROOM_PIPELINE_TEMPLATES_PATH", "").split(os.pathsep)
    additionalPipelinesPath = [i for i in additionalPipelinesPath if i]
    pipelineTemplatesFolders = [os.path.join(meshroomFolder, 'pipelines')] + additionalPipelinesPath
    for f in pipelineTemplatesFolders:
        if os.path.isdir(f):
            loadPipelineTemplates(f)
        else:
            logging.error("Pipeline templates folder '{}' does not exist.".format(f))
