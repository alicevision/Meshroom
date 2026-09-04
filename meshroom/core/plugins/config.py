from __future__ import annotations

import json
import logging
import os
import re

from pathlib import Path
from typing import NamedTuple, Optional

# Plugin name pattern for config.json.
# Only letters and digits are allowed.
_NAME_PATTERN = re.compile(r"^[A-Za-z0-9]+$")

# Plugin version pattern for config.json.
# Only letters and digits are allowed or "major.minor.patch".
_VERSION_PATTERN = re.compile(r"^([A-Za-z0-9]+|\d+\.\d+\.\d+)$")


class PluginConfig(NamedTuple):
    """
    The parsed content of a plugin's "config.json" file.

    Members:
        name: the plugin's name, if provided and valid. None if absent, invalid, or not
              applicable (e.g. only an env list).
        version: the plugin's version, if provided and valid. None if absent, invalid, or not
              applicable (e.g. only an env list).
        env: the list of environment variable entries declared in the file (at the top level
              of the file, or under the "env" key).
    """
    name: Optional[str]
    version: Optional[str]
    env: list[dict]

    def resolveEnv(self, basePath: Path, pluginName: str) -> dict[str, str]:
        """
        Resolve "env" into a dictionary of environment variable names to values.

        Args:
            basePath: the folder to resolve against when entry value is not absolute.
            pluginName: the name of the plugin "env" belongs to, used in log messages.

        Returns:
            dict[str, str]: the resolved environment variables.
        """
        configEnv: dict[str, str] = {}
        for entry in self.env:
            # An entry is expected to be formatted as follows:
            # { "key": "key_of_var", "type": "type_of_value", "value": "var_value" }
            # If "type" is not provided, it is assumed to be "string"
            k = entry.get("key", None)
            t = entry.get("type", None)
            val = entry.get("value", None)

            if not k or not val:
                logging.warning(f"Invalid entry in configuration file for {pluginName}: {entry}.")
                continue

            if t == "path":
                if os.path.isabs(val):
                    resolvedPath = Path(val).resolve()
                else:
                    resolvedPath = Path(os.path.join(basePath, val)).resolve()

                if resolvedPath.exists():
                    val = resolvedPath.as_posix()
                else:
                    logging.debug(f"{k}: {resolvedPath.as_posix()} does not exist "
                                  f"(path before resolution: {val}).")

            configEnv[k] = str(val)

        return configEnv

    @staticmethod
    def load(configPath: Path) -> PluginConfig:
        """
        Parse the plugin configuration file at "configPath" into a PluginConfig.

        The file can either be:
        - a plain list of environment variable entries (array), in which case "name"
            and "version" are None.
        - an object with optional "name" (str), "version" (str), and "env"
            (list of environment variable) keys.

        Args:
            configPath: the absolute path of the "config.json" file to parse.

        Returns:
            PluginConfig: the parsed configuration.
        """
        try:
            with open(configPath) as configFile:
                content = json.load(configFile)
        except FileNotFoundError:
            logging.debug(f"No configuration file 'config.json' was found at '{configPath}'.")
            return PluginConfig(None, None, [])
        except json.JSONDecodeError as err:
            logging.error(f"Malformed JSON in the configuration file '{configPath}': {err}")
            return PluginConfig(None, None, [])
        except IOError as err:
            logging.error(f"Error while accessing the configuration file '{configPath}': {err}")
            return PluginConfig(None, None, [])

        if isinstance(content, list):
            return PluginConfig(None, None, content)

        if not isinstance(content, dict):
            logging.warning(f"Configuration file '{configPath}' must contain a list or an object, "
                            f"got {type(content).__name__}. Ignoring it.")
            return PluginConfig(None, None, [])

        env = content.get("env", [])
        if not isinstance(env, list):
            logging.warning(f"'env' in configuration file '{configPath}' must be a list, "
                            f"got {type(env).__name__}. Ignoring it.")
            env = []

        return PluginConfig(
            PluginConfig._sanitizeName(content.get("name"), configPath),
            PluginConfig._sanitizeVersion(content.get("version"), configPath),
            env,
        )

    @staticmethod
    def _sanitizeName(name, configPath: Path) -> Optional[str]:
        """
        Return "name" if it only contains letters and digits, None otherwise.
        """
        if name is None:
            return None
        if not isinstance(name, str) or not _NAME_PATTERN.match(name):
            logging.warning(f"Invalid 'name' in configuration file '{configPath}': {name!r}. "
                            f"Plugin names must only contain letters and digits. Ignoring it.")
            return None
        return name

    @staticmethod
    def _sanitizeVersion(version, configPath: Path) -> Optional[str]:
        """
        Return "version" if it only contains letters and digits, or follows "major.minor.micro",
        None otherwise.
        """
        if version is None:
            return None
        if not isinstance(version, str) or not _VERSION_PATTERN.match(version):
            logging.warning(f"Invalid 'version' in configuration file '{configPath}': {version!r}. "
                            f"Versions must only contain letters and digits, or follow "
                            f"'major.minor.micro'. Ignoring it.")
            return None
        return version
