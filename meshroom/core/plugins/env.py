from __future__ import annotations

import glob
import logging
import os
import re
import sys

from enum import Enum
from pathlib import Path

from meshroom.common import BaseObject
from meshroom import _MESHROOM_ROOT
from meshroom.core.desc.node import _MESHROOM_COMPUTE_DEPS


class ProcessEnvType(Enum):
    """ Supported process environments. """
    DIRTREE = "dirtree",
    REZ = "rez"


class ProcessEnv(BaseObject):
    """
    Describes the environment required by a node's process.

    Args:
        folder: the source folder for the process.
        configEnv: the dictionary containing the environment variables defined in a configuration file
                   for the process to run.
        pluginName: the name of the plugin object.
        envType: (optional) the type of process environment.
        uri: (optional) the Unique Resource Identifier to activate the environment.
    """

    def __init__(self, folder: str, configEnv: dict[str, str], pluginName: str,
                 envType: ProcessEnvType = ProcessEnvType.DIRTREE, uri: str = ""):
        super().__init__()
        self._folder: str = folder
        self._configEnv: dict[str: str] = configEnv
        self.pluginName: str = pluginName
        self._processEnvType: ProcessEnvType = envType
        self.uri: str = uri
        self._env: dict = None

    def getEnvDict(self) -> dict:
        """ Return the environment dictionary if it has been modified, None otherwise. """
        return self._env

    def getCommandPrefix(self) -> str:
        """ Return the prefix to the command line that will be executed by the process. """
        return ""

    def getCommandSuffix(self) -> str:
        """ Return the suffix to the command line that will be executed by the process. """
        return ""


class DirTreeProcessEnv(ProcessEnv):
    """
    """
    def __init__(self, folder: str, configEnv: dict[str: str], pluginName: str):
        super().__init__(folder, configEnv, pluginName, envType=ProcessEnvType.DIRTREE)

        # If there is a virtual environment, it is expected to be named "venv".
        # Beside the virtual environment, a standard "bin"/"lib"/"lib64" hierarchy at
        # the top level of the plugin folder is expected.
        venvFolder = Path(folder, "venv")

        # Find all the libs that are not directly at the "lib*"-level
        envLibPaths = glob.glob(f'{folder}/lib*/python[0-9].[0-9]*/site-packages',
                                recursive=False)
        venvLibPaths = glob.glob(f'{venvFolder}/lib*/python[0-9].[0-9]*/site-packages',
                                 recursive=False)

        self.binPaths: list = [str(Path(folder, "bin")), str(Path(venvFolder, "bin"))]
        self.libPaths: list = [str(Path(folder, "lib")), str(Path(folder, "lib64")),
                               str(Path(venvFolder, "lib")), str(Path(venvFolder, "lib64"))]
        self.pythonPaths: list = [str(Path(folder)), str(Path(venvFolder))] + \
                                 self.binPaths + envLibPaths + venvLibPaths

        if sys.platform == "win32":
            # For Windows platforms, try and include the content of the virtual env if it exists
            # The virtual env is expected to be named "venv"
            venvLibPath = Path(venvFolder, "Lib", "site-packages")
            if venvLibPath.exists():
                self.pythonPaths.append(venvLibPath.as_posix())
        else:
            # For Linux platforms, lib paths may need to be discovered recursively to be properly
            # added to LD_LIBRARY_PATH
            extraLibPaths = []
            regex = re.compile(r"^lib(\d{2})?$")
            for envPath in envLibPaths + venvLibPaths:
                for path, directories, _ in os.walk(envPath):
                    for directory in directories:
                        if re.match(regex, directory):
                            extraLibPaths.append(os.path.join(path, directory))
            self.libPaths = self.libPaths + extraLibPaths

        # Setup the environment dictionary
        self._env = os.environ.copy()
        self._env["PYTHONPATH"] = os.pathsep.join(
            [f"{_MESHROOM_ROOT}"] + self.pythonPaths + [os.getenv('PYTHONPATH', '')])
        self._env["LD_LIBRARY_PATH"] = f"{os.pathsep.join(self.libPaths)}{os.pathsep}{os.getenv('LD_LIBRARY_PATH', '')}"
        self._env["PATH"] = f"{os.pathsep.join(self.binPaths)}{os.pathsep}{os.getenv('PATH', '')}"

        for k, val in self._configEnv.items():
            # Preserve user-defined environment variables:
            # manually set environment variable values take precedence over config file defaults.
            if k in self._env:
                continue

            self._env[k] = val


class RezProcessEnv(ProcessEnv):
    """
    """

    REZ_DELIMITER_PATTERN = re.compile(r"-|==|>=|>|<=|<")

    def __init__(self, folder: str, configEnv: dict[str: str], pluginName: str, uri: str = ""):
        if not uri:
            raise RuntimeError("Missing name of the Rez environment needs to be provided.")
        super().__init__(folder, configEnv, pluginName, envType=ProcessEnvType.REZ, uri=uri)

    def resolveRezSubrequires(self) -> list[str]:
        """
        Return the list of packages defined for the node execution. These execution packages are
        named subrequires.
        Note: If a package does not have a version number, the version is aligned with the main
        Meshroom environment (if this package is defined).
        """
        if os.getenv(f"{self.uri.upper()}_{self.pluginName.upper()}_SUBREQUIRES"):
            subrequires = os.environ.get(f"{self.uri.upper()}_{self.pluginName.upper()}_SUBREQUIRES", "").split(os.pathsep)
        else:
            subrequires = os.environ.get(f"{self.uri.upper()}_SUBREQUIRES", "").split(os.pathsep)
        if not subrequires:
            return []

        packages = []
        # Packages that are resolved in the current environment
        currentEnvPackages = []
        resolvedVersions = {}
        if "REZ_USED_RESOLVE" in os.environ:
            resolvedPackages = os.getenv("REZ_USED_RESOLVE", "").split()
            for package in resolvedPackages:
                if package.startswith("~"):
                    continue
                currentEnvPackages.append(package)
                name, version = self.REZ_DELIMITER_PATTERN.split(package, maxsplit=1)
                resolvedVersions[name] = version
        logging.debug("Packages in the current environment: " + ", ".join(currentEnvPackages))

        # Take packages with the set versions for those which have one, and try to take packages
        # in the current environment (if they are resolved in it)
        for package in subrequires:
            packageTuple = self.REZ_DELIMITER_PATTERN.split(package, maxsplit=1)
            if len(packageTuple) == 1:
                # Only the package name in the subrequires.
                # Search for a corresponding version in the parent environment.
                packageName = packageTuple[0]
                parentResolvedVersion = resolvedVersions.get(packageName)
                if parentResolvedVersion:
                    packages.append(f"{packageName}=={parentResolvedVersion}")
                else:
                    packages.append(package)
            elif len(packageTuple) == 2:
                # The subrequires ask for a specific version
                packages.append(package)

        def extractPackageName(packageString: str) -> str:
            return self.REZ_DELIMITER_PATTERN.split(packageString, maxsplit=1)[0]
        packageNames = [extractPackageName(package) for package in packages]

        for package in _MESHROOM_COMPUTE_DEPS:
            # For packages that are required by meshroom_compute, do not specify any version
            # or align it with Meshroom's: the version will be found during the resolution of
            # the environment based on the other packages.
            # If any of these packages is already part of the environment a plugin's dependency,
            # do not add it
            if package not in packageNames:
                packages.append(package)

        logging.debug("Packages for the execution environment: " + ", ".join(packages))
        return packages

    def getCommandPrefix(self):
        # TODO: make Windows-compatible

        # Retrieve the global PYTHONPATH and append to the subrequires' environment (which will only be resolved inside
        # the execution environment).
        # This will allow loading properly descriptions for nodes from other plugins that may have imports that
        # cannot be resolved from the subrequires' PYTHONPATH alone.
        currentPythonPaths = os.environ.get("PYTHONPATH", "")
        pythonPaths = f"{os.pathsep.join(['$PYTHONPATH', f'{_MESHROOM_ROOT}', f'{self._folder}', f'{currentPythonPaths}'])}"

        # Retrieve the loaded plugins and nodes to re-inject them in the subrequires' environment.
        # In most cases, this is overkill as these variables are inherited by rez, but there might be some
        # cases where a package in the subrequires' environment edits one of these variables, which will
        # reset it.
        rezPlugins = os.environ.get("MESHROOM_REZ_PLUGINS", "")
        regPlugins = os.environ.get("MESHROOM_PLUGINS_PATH", "")
        rezUserPlugins = os.environ.get("MESHROOM_USER_REZ_PLUGINS", "")
        regUserPlugins = os.environ.get("MESHROOM_USER_PLUGINS_PATH", "")
        meshroomNodesPath = os.environ.get("MESHROOM_NODES_PATH", "")

        return f"rez env {' '.join(self.resolveRezSubrequires())} " \
               f"-c 'PYTHONPATH={pythonPaths} MESHROOM_REZ_PLUGINS={rezPlugins} " \
               f"MESHROOM_PLUGINS_PATH={regPlugins} MESHROOM_USER_PLUGINS_PATH={regUserPlugins} " \
               f"MESHROOM_USER_REZ_PLUGINS={rezUserPlugins} MESHROOM_NODES_PATH={meshroomNodesPath} "

    def getCommandSuffix(self):
        return "'"


def processEnvFactory(folder: str, configEnv: dict[str: str], pluginName: str, envType: str = "dirtree", uri: str = "") -> ProcessEnv:
    if envType == "dirtree":
        return DirTreeProcessEnv(folder, configEnv, pluginName)
    return RezProcessEnv(folder, configEnv, pluginName, uri=uri)
