"""
Meshroom environment variable management.
"""

__all__ = [
    "EnvVar",
    "EnvVarHelpAction",
]

import argparse
import os
from dataclasses import dataclass
from enum import Enum
import sys
from typing import Any, Type


@dataclass
class VarDefinition:
    """Environment variable definition."""

    # The type to cast the value to.
    valueType: Type
    # Default value if the variable is not set in the environment.
    default: str
    # Description of the purpose of the variable.
    description: str = ""

    def __str__(self) -> str:
        return f"{self.description} ({self.valueType.__name__}, default: '{self.default}')"


class EnvVar(Enum):
    """Meshroom environment variables catalog."""

    # UI - Debug
    MESHROOM_QML_DEBUG = VarDefinition(bool, "False", "Enable QML debugging")
    MESHROOM_QML_DEBUG_PARAMS = VarDefinition(
        str, "port:3768", "QML debugging params as expected by -qmljsdebugger"
    )

    @staticmethod
    def get(envVar: "EnvVar") -> Any:
        """Get the value of `envVar`, cast to the variable type."""
        value = os.environ.get(envVar.name, envVar.value.default)
        return EnvVar._cast(value, envVar.value.valueType)

    @staticmethod
    def _cast(value: str, valueType: Type) -> Any:
        if valueType is str:
            return value
        elif valueType is bool:
            return value.lower() in {"true", "1", "on"}
        return valueType(value)

    @classmethod
    def help(cls) -> str:
        """Return a formatted string with the details of each environment variables."""
        return "\n".join([f"{var.name}: {var.value}" for var in cls])


class EnvVarHelpAction(argparse.Action):
    """Argparse action for printing Meshroom environment variables help and exit."""

    DEFAULT_HELP = "Print Meshroom environment variables help and exit."

    def __call__(self, parser, namespace, value, option_string=None):
        print("Meshroom environment variables:")
        print(EnvVar.help())
        sys.exit(0)
