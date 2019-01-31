__version__ = "2018.1.0"

import os
# Allow override from env variable
__version__ = os.environ.get("REZ_MESHROOM_VERSION", __version__)

import logging
from enum import Enum


class Backend(Enum):
    STANDALONE = 1
    PYSIDE = 2


backend = Backend.STANDALONE


def useUI():
    global backend
    backend = Backend.PYSIDE


def setupEnvironment():
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

    import os
    import sys

    def addToEnvPath(var, val, index=-1):
        """
        Add paths to the given environment variable.

        Args:
            var (str): the name of the variable to add paths to
            val (str or list of str): the path(s) to add
            index (int): insertion index
        """
        paths = os.environ.get(var, "").split(os.pathsep)

        if not isinstance(val, (list, tuple)):
            val = [val]

        paths[index:index] = val
        os.environ[var] = os.pathsep.join(paths)

    # sys.frozen is initialized by cx_Freeze
    isFrozen = getattr(sys, "frozen", False)
    # setup root directory (override possible by setting "MESHROOM_INSTALL_DIR" environment variable)
    rootDir = os.path.dirname(sys.executable) if isFrozen else os.environ.get("MESHROOM_INSTALL_DIR", None)

    if rootDir:
        os.environ["MESHROOM_INSTALL_DIR"] = rootDir

        aliceVisionDir = os.path.join(rootDir, "aliceVision")
        # default directories
        aliceVisionBinDir = os.path.join(aliceVisionDir, "bin")
        aliceVisionShareDir = os.path.join(aliceVisionDir, "share", "aliceVision")
        qtPluginsDir = os.path.join(rootDir, "qtPlugins")
        sensorDBPath = os.path.join(aliceVisionShareDir, "cameraSensors.db")
        voctreePath = os.path.join(aliceVisionShareDir, "vlfeat_K80L3.SIFT.tree")

        env = {
            'PATH': aliceVisionBinDir,
            'QT_PLUGIN_PATH': [qtPluginsDir],
            'QML2_IMPORT_PATH': [os.path.join(qtPluginsDir, "qml")]
        }

        for key, value in env.items():
            logging.info("Add to {}: {}".format(key, value))
            addToEnvPath(key, value, 0)

        variables = {
            "ALICEVISION_SENSOR_DB": sensorDBPath,
            "ALICEVISION_VOCTREE": voctreePath
        }

        for key, value in variables.items():
            if key not in os.environ and os.path.exists(value):
                logging.info("Set {}: {}".format(key, value))
                os.environ[key] = value
