import hashlib
from contextlib import contextmanager
import importlib
import inspect
import os
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
except Exception:
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
pipelineTemplates = {}


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

                importPlugin = True
                for p in plugins:
                    if classType == desc.Node:
                        nodeErrors = validateNodeDesc(p)
                        if nodeErrors:
                            errors.append("  * {}: The following parameters do not have valid default values/ranges: {}"
                                          .format(pluginName, ", ".join(nodeErrors)))
                            importPlugin = False
                            break
                    p.packageName = packageName
                    p.packageVersion = packageVersion
                if importPlugin:
                    pluginTypes.extend(plugins)
            except Exception as e:
                errors.append('  * {}: {}'.format(pluginName, str(e)))

    if errors:
        logging.warning('== The following "{package}" plugins could not be loaded ==\n'
                        '{errorMsg}\n'
                        .format(package=packageName, errorMsg='\n'.join(errors)))
    return pluginTypes


def validateNodeDesc(nodeDesc):
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
        nodeDesc (desc.Node): description of the node

    Returns:
        errors (list): the list of invalid parameters if there are any, empty list otherwise
    """
    errors = []

    for param in nodeDesc.inputs:
        err = param.checkValueTypes()
        if err:
            errors.append(err)

    for param in nodeDesc.outputs:
        if param.value is None:
            continue
        err = param.checkValueTypes()
        if err:
            errors.append(err)

    return errors


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
            if isinstance(versionName, str):
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
    global nodesDesc
    if nodeType.__name__ in nodesDesc:
        logging.error("Node Desc {} is already registered.".format(nodeType.__name__))
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
            logging.debug('Nodes loaded [{}]: {}'.format(package, ', '.join([nodeType.__name__ for nodeType in nodeTypes])))


def registerSubmitter(s):
    global submitters
    if s.name in submitters:
        logging.error("Submitter {} is already registered.".format(s.name))
    submitters[s.name] = s


def loadSubmitters(folder, packageName):
    return loadPlugins(folder, packageName, BaseSubmitter)


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
