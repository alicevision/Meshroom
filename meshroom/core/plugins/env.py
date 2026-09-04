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


def processEnvFactory(folder: str, configEnv: dict[str, str], pluginName: str, pluginSubPackage: str = None,
                      envType: str = "dirtree") -> ProcessEnv:
    """
    Create the ProcessEnv matching "envType" for a plugin.

    Args:
        folder: the source folder for the process.
        configEnv: the dictionary containing the environment variables defined in a configuration file
                   for the process to run.
        pluginName: the name of the plugin object.
        pluginSubPackage: the dotted path, relative to the plugin's root, of the package containing
                          the node/submitter class this environment is built for, if any.
        envType: "dirtree" to build a DirTreeProcessEnv, "rez" build a RezProcessEnv.

    Returns:
        ProcessEnv: the created DirTreeProcessEnv or RezProcessEnv.
    """
    if envType == "dirtree":
        return DirTreeProcessEnv(folder, configEnv, pluginName, pluginSubPackage)
    return RezProcessEnv(folder, configEnv, pluginName, pluginSubPackage)


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
        pluginSubPackage: (optional) the dotted path, relative to the plugin's root, of the package
                          containing the node/submitter class this environment is built for.
        envType: (optional) the type of process environment.
    """

    def __init__(self, folder: str, configEnv: dict[str, str], pluginName: str, pluginSubPackage: str = None,
                 envType: ProcessEnvType = ProcessEnvType.DIRTREE):
        super().__init__()
        self._folder: str = folder
        self._configEnv: dict[str, str] = configEnv
        self.pluginName: str = pluginName
        self.pluginSubPackage: str = pluginSubPackage
        self._processEnvType: ProcessEnvType = envType
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
    A ProcessEnv built from a plain directory tree: PYTHONPATH/LD_LIBRARY_PATH/PATH are assembled
    from the plugin's "bin"/"lib"/"lib64" folders and, if present, its "venv" virtual environment.
    """
    def __init__(self, folder: str, configEnv: dict[str, str], pluginName: str, pluginSubPackage: str):
        super().__init__(folder, configEnv, pluginName, pluginSubPackage, envType=ProcessEnvType.DIRTREE)

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
    A ProcessEnv built by resolving a Rez environment for the plugin's subrequires, activated
    through a "rez env" command prefix/suffix wrapped around the node's command line.
    """

    REZ_DELIMITER_PATTERN = re.compile(r"-|==|>=|>|<=|<")

    def __init__(self, folder: str, configEnv: dict[str, str], pluginName: str, pluginSubPackage: str):
        if not pluginName:
            raise RuntimeError("Missing name of the Rez environment needs to be provided.")
        super().__init__(folder, configEnv, pluginName, pluginSubPackage, envType=ProcessEnvType.REZ)

    def resolveRezSubrequires(self) -> list[str]:
        """
        Return the list of packages defined for the node execution. These execution packages are
        named subrequires.
        Note: If a package does not have a version number, the version is aligned with the main
        Meshroom environment (if this package is defined).
        """
        pluginNameUpper = self.pluginName.upper()
        pluginSubPackageUpper = None

        if self.pluginSubPackage:
            pluginSubPackageUpper = self.pluginSubPackage.split('.', 1)[0].upper()  # first level sub package

        if pluginSubPackageUpper and os.getenv(f"{pluginNameUpper}_{pluginSubPackageUpper}_SUBREQUIRES"):
            subrequires = os.environ.get(f"{pluginNameUpper}_{pluginSubPackageUpper}_SUBREQUIRES", "").split(os.pathsep)
        else:
            subrequires = os.environ.get(f"{pluginNameUpper}_SUBREQUIRES", "").split(os.pathsep)
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

        # Use the PYTHONPATH from the subrequires' environment (which will only be resolved once
        # inside the execution environment) and add MESHROOM_ROOT and the plugin's folder itself
        # to it
        pythonPaths = f"{os.pathsep.join(['$PYTHONPATH', f'{_MESHROOM_ROOT}', f'{self._folder}'])}"

        return f"rez env {' '.join(self.resolveRezSubrequires())} -c 'PYTHONPATH={pythonPaths} "

    def getCommandSuffix(self):
        return "'"
