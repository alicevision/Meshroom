from distutils import util
from enum import Enum
import logging
import os
import sys
import platform

class VersionStatus(Enum):
    release = 1
    develop = 2

__version__ = "2023.2.0"
# Always increase the minor version when switching from release to develop.
__version_status__ = VersionStatus.develop

if __version_status__ is VersionStatus.develop:
    __version__ += "-" + __version_status__.name

__version_label__ = __version__
# Modify version label if we are in a development phase.
if __version_status__ is VersionStatus.develop:

    scriptPath = os.path.dirname(os.path.abspath(__file__))
    headFilepath = os.path.join(scriptPath, "../.git/HEAD")
    if os.path.exists(headFilepath):
        # Add git branch name, if it is a git repository
        with open(headFilepath, "r") as headFile:
            data = headFile.readlines()
            branchName = data[0].split('/')[-1].strip()
            __version_label__ += " branch=" + branchName
    else:
        # Add a generic default label "develop"
        __version_label__ += "-" + __version_status__.name

    # Allow override from env variable
    if "REZ_MESHROOM_VERSION" in os.environ:
        __version_label__ += " package=" + os.environ.get("REZ_MESHROOM_VERSION")


# Internal imports after the definition of the version
from .common import init, Backend

# sys.frozen is initialized by cx_Freeze and identifies a release package
isFrozen = getattr(sys, "frozen", False)

useMultiChunks = util.strtobool(os.environ.get("MESHROOM_USE_MULTI_CHUNKS", "True"))

logStringToPython = {
    'fatal': logging.FATAL,
    'error': logging.ERROR,
    'warning': logging.WARNING,
    'info': logging.INFO,
    'debug': logging.DEBUG,
    'trace': logging.DEBUG,
}
logging.getLogger().setLevel(logStringToPython[os.environ.get('MESHROOM_VERBOSE', 'warning')])

def setupEnvironment(backend=Backend.STANDALONE):
    """
    Setup environment for Meshroom to work in a prebuilt, standalone configuration.

    Use 'MESHROOM_INSTALL_DIR' to simulate standalone configuration with a path to a Meshroom installation folder.

    Directories or files can be overwritten by using the corresponding environment variable.

    Example: (unix) $ export ALICEVISION_LIB=aliceVision/lib:aliceVision/lib64

    # Meshroom standalone structure

    - Meshroom/         # <MESHROOM_INSTALL_DIR>
       - aliceVision/   # <ALICEVISION_ROOT>
           - bin/    # <ALICEVISION_BIN_PATH> runtime bundled binaries (windows: exe + libs, unix: executables)
           - lib/    # <ALICEVISION_LIB> runtime bundled libraries (unix: libs)
           - share/  # resource files
               - aliceVision/
                   - COPYING.md         # AliceVision COPYING file
                   - cameraSensors.db   # <ALICEVISION_SENSOR_DB> sensor database
                   - vlfeat_K80L3.tree  # <ALICEVISION_VOCTREE> voctree file
                   - config.ocio        # <ALICEVISION_OCIO> AliceVision color configuration file
       - lib/      # Python lib folder
       - qtPlugins/  # <QT_PLUGIN_PATH>
            - qml/   # <QML2_IMPORT_PATH>
       Meshroom    # main executable
       COPYING.md  # Meshroom COPYING file
       CHANGES.md   # Meshroom changelog file
    """

    init(backend)

    class _env_var:
        """Container class for environment variable information."""
        def __init__(self, name, default, isFile=False, appendTo=None):
            """
            Args:
                name (str): the name of the variable
                default (callable -> str): default value
                isFile (bool): specifies if it's a file or a directory
                appendTo (str): environment variable to be appended to.
            """
            self.name = name
            self.default = default
            self.isFile = isFile
            self.appendTo = appendTo
            self.__value = None

        @property
        def value(self):
            return self.__value

        def resolveValue(self):
            """Resolve environment value using current environment and default.
            
            Also check if the resolved path exists.
            """
            check = os.path.isfile if self.isFile else os.path.isdir
            self.__value = os.environ.get(self.name, None)
            if self.__value is None:
                logging.debug("{} is not defined. Trying to retrieve default path.".format(self.name))
                self.__value = self.default()
                usingDefault = True
            else:
                usingDefault = False
            if not all(check(x) for x in self.__value.split(os.pathsep)):
                if usingDefault:
                    logging.warning("Couldn't find {} at default path(s): {}".format(self.name, self.__value))
                    # val = None
                else:
                    # TODO error or warning?
                    logging.error("{} is set but the path(s) cannot be found: {}".format(self.name, self.__value))
            logging.debug("{} is set to: {}".format(self.name, self.__value))
        
        def updateEnv(self):
            """Update environment with this variable after resolving its value."""
            self.resolveValue()
            if self.__value is None:
                return
            os.environ[self.name] = self.__value
            if self.appendTo is not None:
                os.environ[self.appendTo] = os.pathsep.join([self.__value, os.environ[self.appendTo]])

    env = {}
    rootDir = None
    # n.b. order is important
    env_vars = [_env_var("MESHROOM_INSTALL_DIR", lambda: rootDir, False),
        _env_var("ALICEVISION_ROOT",
            lambda: os.path.join(env["MESHROOM_INSTALL_DIR"].value, "aliceVision"),
            False),
        _env_var("ALICEVISION_BIN_PATH",
            lambda: os.path.join(env["ALICEVISION_ROOT"].value, "bin"),
            False,
            "PATH"),
        _env_var("ALICEVISION_SENSOR_DB",
            lambda: os.path.join(env["ALICEVISION_ROOT"].value, "share", "aliceVision", "cameraSensors.db"),
            True),
        _env_var("ALICEVISION_VOCTREE",
            lambda: os.path.join(env["ALICEVISION_ROOT"].value, "share", "aliceVision", "vlfeat_K80L3.tree"),
            True),
        _env_var("ALICEVISION_OCIO",
            lambda: os.path.join(env["ALICEVISION_ROOT"].value, "share", "aliceVision", "config.ocio"),
            True),
        _env_var("QT_PLUGIN_PATH",
            lambda: os.path.join(env["MESHROOM_INSTALL_DIR"].value, "qtPlugins"),
            False),
        _env_var("QML2_IMPORT_PATH",
            lambda: os.path.join(env["MESHROOM_INSTALL_DIR"], "qtPlugins", "qml"),
            False)]
    if not isFrozen and platform.system() in ("Linux", "Darwin"):
        env_vars += [_env_var("ALICEVISION_LIB",
            lambda: os.pathsep.join([
                os.path.join(env["ALICEVISION_ROOT"].value, "lib"),
                os.path.join(env["ALICEVISION_ROOT"].value, "lib64")]),
            False,
            "LD_LIBRARY_PATH")]

    if isFrozen:
        rootDir = os.path.dirname(sys.executable)
    else:
        rootDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = { var.name: var for var in env_vars}

    for key in env:
        env[key].updateEnv()
