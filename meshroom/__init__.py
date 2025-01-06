from distutils import util
from enum import Enum
import logging
import os
import sys


class VersionStatus(Enum):
    release = 1
    develop = 2


__version__ = "2025.1.0"
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
    elif "ION_MESHROOM_VERSION" in os.environ:
        __version_label__ += " container=" + os.environ.get("ION_MESHROOM_VERSION")


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

    # Meshroom standalone structure

    - Meshroom/
       - aliceVision/
           - bin/    # runtime bundled binaries (windows: exe + libs, unix: executables)
           - lib/    # runtime bundled libraries (unix: libs)
           - share/  # resource files
               - aliceVision/
                   - COPYING.md         # AliceVision COPYING file
                   - cameraSensors.db   # sensor database
                   - vlfeat_K80L3.tree  # voctree file
       - lib/      # Python lib folder
       - qtPlugins/
       Meshroom    # main executable
       COPYING.md  # Meshroom COPYING file
    """

    init(backend)

    def addToEnvPath(var, val, index=-1):
        """
        Add paths to the given environment variable.

        Args:
            var (str): the name of the variable to add paths to
            val (str or list of str): the path(s) to add
            index (int): insertion index
        """
        if not val:
            return

        paths = os.environ.get(var, "").split(os.pathsep)

        if not isinstance(val, (list, tuple)):
            val = [val]

        if index == -1:
            paths.extend(val)
        elif index == 0:
            paths = val + paths
        else:
            raise ValueError("addToEnvPath: index must be -1 or 0.")
        os.environ[var] = os.pathsep.join(paths)

    # setup root directory (override possible by setting "MESHROOM_INSTALL_DIR" environment variable)
    rootDir = os.path.dirname(sys.executable) if isFrozen else os.environ.get("MESHROOM_INSTALL_DIR", None)
    logging.debug(f"isFrozen={isFrozen}")
    logging.debug(f"sys.executable={sys.executable}")
    logging.debug(f"rootDir={rootDir}")

    if rootDir:
        os.environ["MESHROOM_INSTALL_DIR"] = rootDir

        aliceVisionDir = os.path.join(rootDir, "aliceVision")
        # default directories
        aliceVisionBinDir = os.path.join(aliceVisionDir, "bin")
        aliceVisionShareDir = os.path.join(aliceVisionDir, "share", "aliceVision")
        qtPluginsDir = os.path.join(rootDir, "qtPlugins")
        sensorDBPath = os.path.join(aliceVisionShareDir, "cameraSensors.db")
        voctreePath = os.path.join(aliceVisionShareDir, "vlfeat_K80L3.SIFT.tree")
        sphereDetectionModel = os.path.join(aliceVisionShareDir, "sphereDetection_Mask-RCNN.onnx")
        semanticSegmentationModel = os.path.join(aliceVisionShareDir, "fcn_resnet50.onnx")

        env = {
            'PATH': aliceVisionBinDir,
            'QT_PLUGIN_PATH': [qtPluginsDir],
            'QML2_IMPORT_PATH': [os.path.join(qtPluginsDir, "qml")]
        }

        for key, value in env.items():
            logging.debug(f"Add to {key}: {value}")
            addToEnvPath(key, value, 0)

        variables = {
            "ALICEVISION_ROOT": aliceVisionDir,
            "ALICEVISION_SENSOR_DB": sensorDBPath,
            "ALICEVISION_VOCTREE": voctreePath,
            "ALICEVISION_SPHERE_DETECTION_MODEL": sphereDetectionModel,
            "ALICEVISION_SEMANTIC_SEGMENTATION_MODEL": semanticSegmentationModel
        }

        for key, value in variables.items():
            if key not in os.environ and os.path.exists(value):
                logging.debug(f"Set {key}: {value}")
                os.environ[key] = value
    else:
        addToEnvPath("PATH", os.environ.get("ALICEVISION_BIN_PATH", ""))


os.environ["QML_XHR_ALLOW_FILE_READ"] = '1'
os.environ["QML_XHR_ALLOW_FILE_WRITE"] = '1'
os.environ["PYSEQ_STRICT_PAD"] = '1'
os.environ["QSG_RHI_BACKEND"] = "opengl"
