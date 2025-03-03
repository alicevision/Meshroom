import os

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path

from dataclasses import dataclass

import meshroom


_MESHROOM_ROOT = Path(meshroom.__file__).parent.parent
_MESHROOM_COMPUTE = _MESHROOM_ROOT / "bin" / "meshroom_compute"


@dataclass
class ProcessEnvironment(ABC):
    """Describes an isolated meshroom compute process environment.

    Attributes:
        name: User-readable name of the environment.
        uri: Unique resource identifier to activate the environment.
    """

    name: str
    uri: str

    @abstractmethod
    def commandLine(self, args: str) -> str:
        """Build Meshroom compute command line from given args to run in this environment."""
        ...

    @staticmethod
    def pythonPath():
        return f"{_MESHROOM_ROOT}:{os.getenv('PYTHONPATH', '')}"


@dataclass
class DefaultEnvironment(ProcessEnvironment):
    """Default environment similar to the main process."""

    def commandLine(self, args: str) -> str:
        return f"{_MESHROOM_COMPUTE} {args}"


@dataclass
class CondaEnvironment(ProcessEnvironment):
    """Conda environment where uri defines the name of the environment."""

    def commandLine(self, args: str) -> str:
        return f"conda run -n {self.uri} {_MESHROOM_COMPUTE} {args}"


@dataclass
class VirtualEnvironment(ProcessEnvironment):
    """Python virtual environment where uri defines the root path of the virtual environment."""

    def commandLine(self, args: str) -> str:
        return f"{self.uri}/bin/python {_MESHROOM_COMPUTE} {args}"


@dataclass
class RezEnvironment(ProcessEnvironment):
    """Rez environment where uri defined either a list of requirements or a .rxt file.

    Attributes:
        pyexe: The python executable to use for starting meshroom compute.
    """

    pyexe: str = "python"

    def commandLine(self, args: str) -> str:
        pythonPathSetup = f"export PYTHONPATH={_MESHROOM_ROOT}:$PYTHONPATH;"

        cmd = f"{pythonPathSetup} {self.pyexe} {_MESHROOM_COMPUTE} {args}"

        if (path := Path(self.uri)).exists() and path.suffix == ".rxt":
            return f"rez env -i {self.uri} -c '{cmd}'"

        return f"rez env {self.uri} -c '{cmd}'"


class ProcessEnvironmentType(Enum):
    DEFAULT = "default"
    CONDA = "conda"
    VIRTUALENV = "venv"
    REZ = "rez"


_ENV_BY_TYPE = {
    ProcessEnvironmentType.DEFAULT: DefaultEnvironment,
    ProcessEnvironmentType.CONDA: CondaEnvironment,
    ProcessEnvironmentType.VIRTUALENV: VirtualEnvironment,
    ProcessEnvironmentType.REZ: RezEnvironment,
}


def processEnvironmentFactory(name: str, type: str, **kwargs) -> ProcessEnvironment:
    """Creates a ProcessEnvironment instance of the given `type`.

    Args:
        name: The name of the environment.
        type: The ProcessEnvironment type.
        **kwargs: Keyword arguments to pass to the ProcessEnvironment constructor.

    Returns:
        The created ProcessEnvironment instance.
    """
    try:
        return _ENV_BY_TYPE[ProcessEnvironmentType(type)](name, **kwargs)
    except (KeyError, ValueError):
        raise KeyError(f"Unvalid environment type: {type}")
