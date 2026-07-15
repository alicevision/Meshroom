import hashlib
import logging
import os
from pathlib import Path
import sys
import uuid

try:
    # for cx_freeze
    import encodings.ascii
    import encodings.idna
    import encodings.utf_8
except Exception:
    pass

from meshroom.core.plugins.manager import PluginManager
from meshroom.core.submitter import BaseSubmitter
from meshroom.env import EnvVar, meshroomFolder
from . import desc
from .desc import MrNodeType

# Setup logging
logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.INFO)

# make a UUID based on the host ID and current time
sessionUid = str(uuid.uuid1())

cacheFolderName = 'MeshroomCache'
pluginManager: PluginManager = PluginManager()
submitters: dict[str, BaseSubmitter] = {}
pipelineTemplates: dict[str, str] = {}


def hashValue(value) -> str:
    """ Hash 'value' using sha1. """
    hashObject = hashlib.sha1(str(value).encode('utf-8'))
    return hashObject.hexdigest()


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
        # If there is a status, it is placed after a "-" (up to Meshroom 2025.1.0) or a "+"
        versionName = versionName.replace("-", "+")  # Keep compatibility for scenes created with 2025.1.0 or older
        splitComponents = versionName.split("+", maxsplit=1)
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


def loadPipelineTemplates(folder: str):
    if not os.path.isdir(folder):
        logging.error(f"Pipeline templates folder '{folder}' does not exist.")
        return
    for file in os.listdir(folder):
        if file.endswith(".mg") and file not in pipelineTemplates:
            pipelineTemplates[os.path.splitext(file)[0]] = os.path.join(folder, file)


def initNodes():
    nodesFolder = os.path.join(meshroomFolder, "nodes")  # Built-in nodes
    additionalNodesFolders = EnvVar.getList(EnvVar.MESHROOM_NODES_PATH)
    for folder in [nodesFolder] + additionalNodesFolders:
        # Determine the plugin name based on the names of the subfolders
        subFolders = sorted(p.name for p in Path(folder).iterdir()
                        if p.is_dir() and not p.name.startswith("__")) if os.path.isdir(folder) else []
        pluginName = "_".join(subFolders) if subFolders else Path(folder).name
        pluginManager.addPluginFromBuiltInFolder(pluginName, folder)


def initSubmitters():
    # For now we do not want meshroom/submitters always loaded
    # submittersFolder = os.path.join(meshroomFolder, "submitters")  # Built-in submitters
    additionalSubmittersFolders = EnvVar.getList(EnvVar.MESHROOM_SUBMITTERS_PATH)
    for folder in additionalSubmittersFolders:
        # Determine the plugin name based on the names of the subfolders
        subFolders = sorted(p.name for p in Path(folder).iterdir()
                        if p.is_dir() and not p.name.startswith("__")) if os.path.isdir(folder) else []
        pluginName = "_".join(subFolders) if subFolders else Path(folder).name
        pluginManager.addPluginFromBuiltInFolder(pluginName, folder)

    submitters.update({provider.name: provider.instance for provider in pluginManager.getSubmitterProviders().values()})


def initPipelines():
    # Load pipeline templates: check in the default folder and any folder the user might have
    # added to the environment variable
    pipelineTemplatesFolders = EnvVar.getList(EnvVar.MESHROOM_PIPELINE_TEMPLATES_PATH)
    for f in pipelineTemplatesFolders:
        loadPipelineTemplates(f)
    pipelineTemplates.update(pluginManager.getPipelineTemplates())


def initPlugins():
    # Plugin paths
    # Using DirTreeProcessEnv
    additionalPluginsPath = EnvVar.getList(EnvVar.MESHROOM_PLUGINS_PATH)
    pluginsFolders = [os.path.join(meshroomFolder, "plugins")] + additionalPluginsPath
    for folder in pluginsFolders:
        # Use folder name as default plugin name
        pluginManager.addPluginFromPath(Path(folder).name, folder, isUserPlugin=False)

    # User plugin paths
    # Using DirTreeProcessEnv
    userPluginsFolders = EnvVar.getList(EnvVar.MESHROOM_USER_PLUGINS_PATH)
    for folder in userPluginsFolders:
        # Use folder name as default plugin name
        pluginManager.addPluginFromPath(Path(folder).name, folder, isUserPlugin=True)

    # Rez plugins
    # Using RezProcessEnv
    rezPluginList = EnvVar.getList(EnvVar.MESHROOM_REZ_PLUGINS)
    for entry in rezPluginList:
        # Use the REZ package name as plugin name
        rezPackageName, rezPackageFolder = entry.split("=")
        pluginManager.addPluginFromRez(rezPackageName, rezPackageFolder, isUserPlugin=False)

    # Rez user plugins
    # Using RezProcessEnv
    rezUserPluginList = EnvVar.getList(EnvVar.MESHROOM_USER_REZ_PLUGINS)
    for entry in rezUserPluginList:
        # Use the REZ package name as plugin name
        rezPackageName, rezPackageFolder = entry.split("=")
        pluginManager.addPluginFromRez(rezPackageName, rezPackageFolder, isUserPlugin=True)
