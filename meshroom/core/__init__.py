from contextlib import contextmanager
import hashlib
import importlib
import inspect
import logging
import os
from pathlib import Path
import pkgutil
import sys
import traceback
import uuid

try:
    # for cx_freeze
    import encodings.ascii
    import encodings.idna
    import encodings.utf_8
except Exception:
    pass

from meshroom.core.plugins import NodePlugin, NodePluginManager, Plugin, processEnvFactory
from meshroom.core.submitter import BaseSubmitter
from meshroom.env import EnvVar, meshroomFolder
from . import desc
from .desc import MrNodeType

# Setup logging
logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.INFO)

# make a UUID based on the host ID and current time
sessionUid = str(uuid.uuid1())

cacheFolderName = 'MeshroomCache'
pluginManager: NodePluginManager = NodePluginManager()
submitters: dict[str, BaseSubmitter] = {}
pipelineTemplates: dict[str, str] = {}


def hashValue(value) -> str:
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


def loadClasses(folder: str, packageName: str, classType: type) -> list[type]:
    """
    Go over the Python module named "packageName" located in "folder" to find files
    that contain classes of type "classType" and return these classes in a list.

    Args:
        folder: the folder to load the module from.
        packageName: the name of the module to look for nodes in.
        classType: the class to look for in the files that are inspected.
    """
    classes = []
    errors = []

    resolvedFolder = str(Path(folder).resolve())
    # temporarily add folder to python path
    with add_to_path(resolvedFolder):
        # import node package

        try:
            package = importlib.import_module(packageName)
            packageName = package.packageName if hasattr(package, "packageName") \
                else package.__name__
            packageVersion = getattr(package, "__version__", None)
            packagePath = os.path.dirname(package.__file__)
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            last_call = tb[-1]
            logging.warning(f'  * Failed to load package "{packageName}" from folder "{resolvedFolder}" ({type(e).__name__}): {str(e)}\n'
                            # filename:lineNumber functionName
                            f'{last_call.filename}:{last_call.lineno} {last_call.name}\n'
                            # line of code with the error
                            f'{last_call.line}'
                            # Full traceback
                            f'\n{traceback.format_exc()}\n\n'
                            )
            return []

        for _, pluginName, _ in pkgutil.iter_modules(package.__path__):
            pluginModuleName = "." + pluginName

            try:
                pluginMod = importlib.import_module(pluginModuleName, package=package.__name__)
                plugins = [plugin for _, plugin in inspect.getmembers(pluginMod, inspect.isclass)
                           if plugin.__module__ == f"{package.__name__}.{pluginName}"
                           and issubclass(plugin, classType)]

                if not plugins:
                    # Only packages/folders have __path__, single module/file do not have it.
                    isPackage = hasattr(pluginMod, "__path__")
                    # Sub-folders/Packages should not raise a warning
                    if not isPackage:
                        logging.warning(f"No class defined in plugin: {package.__name__}.{pluginName} ('{pluginMod.__file__}')")

                for p in plugins:
                    p.packageName = packageName
                    p.packageVersion = packageVersion
                    p.packagePath = packagePath
                    if classType == desc.BaseNode:
                        nodePlugin = NodePlugin(p)
                        if nodePlugin.errors:
                            errors.append("  * {}: The following parameters do not have valid " \
                                          "default values/ranges: {}".format(pluginName, ", ".join(nodePlugin.errors)))
                        classes.append(nodePlugin)
                    else:
                        classes.append(p)
            except Exception as e:
                tb = traceback.extract_tb(e.__traceback__)
                last_call = tb[-1]
                errors.append(f'  * {pluginName} ({type(e).__name__}): {e}\n'
                              # filename:lineNumber functionName
                              f'{last_call.filename}:{last_call.lineno} {last_call.name}\n'
                              # line of code with the error
                              f'{last_call.line}'
                              # Full traceback
                              f'\n{traceback.format_exc()}\n\n'
                              )

    if errors:
        logging.warning(' The following "{package}" plugins could not be loaded:\n'
                        '{errorMsg}\n'
                        .format(package=packageName, errorMsg='\n'.join(errors)))

    return classes


def loadClassesNodes(folder: str, packageName: str) -> list[NodePlugin]:
    """
    Return the list of all the NodePlugins that were created following the search of the
    Python module named "packageName" located in the folder "folder".
    A NodePlugin is created when a file within "packageName" that contains a class inheriting
    desc.BaseNode is found.

    Args:
        folder: the folder to load the module from.
        packageName: the name of the module to look for nodes in.

    Returns:
        list[NodePlugin]: a list of all the NodePlugins that were created based on the
                          module's search. If none has been created, an empty list is returned.
    """
    return loadClasses(folder, packageName, desc.BaseNode)


def loadClassesSubmitters(folder: str, packageName: str) -> list[BaseSubmitter]:
    """
    Return the list of all the submitters that were found during the search of the
    Python module named "packageName" that located in the folder "folder".
    A submitter is found if a file within "packageName" contains a class inheriting
    from BaseSubmitter.

    Args:
        folder: the folder to load the module from.
        packageName: the name of the module to look for nodes in.

    Returns:
        list[BaseSubmitter]: a list of all the submitters that were found during the
                             module's search
    """
    return loadClasses(folder, packageName, BaseSubmitter)


class Version:
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
            self.status = ''
        elif len(args) == 1:
            versionName = args[0]
            if isinstance(versionName, str):
                self.components, self.status = Version.toComponents(versionName)
            elif isinstance(versionName, (list, tuple)):
                self.components = tuple([int(v) for v in versionName])
                self.status = ''
            else:
                raise RuntimeError("Version: Unsupported input type.")
        else:
            self.components = tuple([int(v) for v in args])
            self.status = ''

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
            return (), ''

        status = ''
        # If there is a status, it is placed after a "-"
        splitComponents = versionName.split("-", maxsplit=1)
        # If there is no status, splitComponents is equal to [versionName]
        if len(splitComponents) > 1:
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


def moduleVersion(moduleName: str, default=None):
    """ Return the version of a module indicated with '__version__' keyword.

    Args:
        moduleName (str): the name of the module to get the version of
        default: the value to return if no version info is available

    Returns:
        str: the version of the module
    """
    return getattr(sys.modules[moduleName], "__version__", default)


def nodeVersion(nodeDesc: desc.Node, default=None):
    """ Return node type version for the given node description class.

    Args:
        nodeDesc (desc.Node): the node description class
        default: the value to return if no version info is available

    Returns:
        str: the version of the node type
    """
    return moduleVersion(nodeDesc.__module__, default)


def loadNodes(folder, packageName) -> list[NodePlugin]:
    if not os.path.isdir(folder):
        logging.error(f"Node folder '{folder}' does not exist.")
        return []

    nodes = loadClassesNodes(folder, packageName)
    return nodes


def loadAllNodes(folder) -> list[Plugin]:
    plugins = []
    for _, package, ispkg in pkgutil.iter_modules([folder]):
        if ispkg:
            plugin = Plugin(package, folder)
            nodePlugins = loadNodes(folder, package)
            if nodePlugins:
                for node in nodePlugins:
                    plugin.addNodePlugin(node)
                nodesStr = ', '.join([node.nodeDescriptor.__name__ for node in nodePlugins])
                logging.debug(f'Nodes loaded [{package}]: {nodesStr}')
                plugins.append(plugin)
    return plugins


def loadPluginFolder(folder) -> list[Plugin]:
    if not os.path.isdir(folder):
        logging.info(f"Plugin folder '{folder}' does not exist.")
        return

    mrFolder = Path(folder, 'meshroom')
    if not mrFolder.exists():
        logging.info(f"Plugin folder '{folder}' does not contain a 'meshroom' folder.")
        return

    plugins = loadAllNodes(folder=mrFolder)
    if plugins:
        for plugin in plugins:
            pluginManager.addPlugin(plugin)
            pipelineTemplates.update(plugin.templates)

    return plugins


def loadPluginsFolder(folder):
    if not os.path.isdir(folder):
        logging.debug(f"PluginSet folder '{folder}' does not exist.")
        return

    for file in os.listdir(folder):
        if os.path.isdir(file):
            subFolder = os.path.join(folder, file)
            loadPluginFolder(subFolder)


def registerSubmitter(s: BaseSubmitter):
    if s.name in submitters:
        logging.error(f"Submitter {s.name} is already registered.")
    submitters[s.name] = s


def loadSubmitters(folder, packageName):
    if not os.path.isdir(folder):
        logging.error(f"Submitters folder '{folder}' does not exist.")
        return

    return loadClassesSubmitters(folder, packageName)


def loadPipelineTemplates(folder: str):
    if not os.path.isdir(folder):
        logging.error(f"Pipeline templates folder '{folder}' does not exist.")
        return
    for file in os.listdir(folder):
        if file.endswith(".mg") and file not in pipelineTemplates:
            pipelineTemplates[os.path.splitext(file)[0]] = os.path.join(folder, file)


def initNodes():
    additionalNodesPath = EnvVar.getList(EnvVar.MESHROOM_NODES_PATH)
    nodesFolders = [os.path.join(meshroomFolder, "nodes")] + additionalNodesPath
    for f in nodesFolders:
        plugins = loadAllNodes(folder=f)
        if plugins:
            for plugin in plugins:
                pluginManager.addPlugin(plugin)


def initSubmitters():
    additionalPaths = EnvVar.getList(EnvVar.MESHROOM_SUBMITTERS_PATH)
    allSubmittersFolders = [meshroomFolder] + additionalPaths
    for folder in allSubmittersFolders:
        subs = loadSubmitters(folder, "submitters")
        for sub in subs:
            registerSubmitter(sub())


def initPipelines():
    # Load pipeline templates: check in the default folder and any folder the user might have
    # added to the environment variable
    pipelineTemplatesFolders = EnvVar.getList(EnvVar.MESHROOM_PIPELINE_TEMPLATES_PATH)
    for f in pipelineTemplatesFolders:
        loadPipelineTemplates(f)
    for plugin in pluginManager.getPlugins().values():
        pipelineTemplates.update(plugin.templates)


def initPlugins():
    # Classic plugins (with a DirTreeProcessEnv)
    additionalPluginsPath = EnvVar.getList(EnvVar.MESHROOM_PLUGINS_PATH)
    pluginsFolders = [os.path.join(meshroomFolder, "plugins")] + additionalPluginsPath
    for f in pluginsFolders:
        plugins = loadPluginFolder(folder=f)
        # Set the ProcessEnv for each plugin
        if plugins:
            for plugin in plugins:
                plugin.processEnv = processEnvFactory(f, plugin.configEnv)

    # Rez plugins (with a RezProcessEnv)
    rezPlugins = initRezPlugins()


def initRezPlugins():
    rezPlugins = {}
    rezList = EnvVar.getList(EnvVar.MESHROOM_REZ_PLUGINS)

    for p in rezList:
        name, path = p.split("=")
        rezPlugins[name] = path  # "name" is the name of the Rez package
        plugins = loadPluginFolder(folder=path)
        # Set the ProcessEnv for Rez plugins
        if plugins:
            for plugin in plugins:
                plugin.processEnv = processEnvFactory(path, plugin.configEnv, envType="rez", uri=name)

    return rezPlugins
