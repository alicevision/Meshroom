from __future__ import annotations

import json
import logging
import os
import re

try:
    # "tomllib" is stdlib from Python 3.11 onward.
    import tomllib
except ImportError:
    # "tomli" (same API) covers 3.9/3.10.
    import tomli as tomllib

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from meshroom.core.files import atomicWriteFile


# Plugin name pattern
# Matching PEP 621's "[project].name" rule:
# - ASCII letters, digits, '.', '-' and '_'.
# - Starting and ending with a letter or digit.
_PLUGIN_NAME_PATTERN = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?$")

# Plugin version pattern.
# Only letters, digits, dots and '+' are allowed.
# e.g. "1.2.3", "v1.2.3", "main+83d0b69".
_PLUGIN_VERSION_PATTERN = re.compile(r"^[A-Za-z0-9.+]+$")

# Plugin publisher pattern.
# Only letters, hyphen, underscore and digits are allowed.
_PLUGIN_PUBLISHER_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


class PluginMetadata:
    """
    Plugin metadata parsed from one of its sources:
    - a plugin "plugin.lock" file.
    - a plugin "pyproject.toml" file.
    - a legacy "meshroom/config.json" file.

    Members:
        name: the plugin's name (if provided and valid).
        version: the plugin's version (if provided and valid).
        publisher: the plugin's publisher (if provided and valid).
        authors: the list of the plugin's authors (if provided, valid string entries only).
        env: the list of environment variable entries declared in the file (if provided and valid).
    """
    def __init__(self, name: Optional[str] = None, version: Optional[str] = None,
                 publisher: Optional[str] = None, authors: Optional[list[str]] = None,
                 env: Optional[list[dict]] = None):
        self.name = name
        self.version = version
        self.publisher = publisher
        self.authors = authors if authors is not None else []
        self.env = env if env is not None else []

    @staticmethod
    def loadJson(path: Path) -> Optional[PluginMetadata]:
        """
        Parse the plugin metadata file at "path" into a PluginMetadata.

        Args:
            path: the absolute path of the metadata file to parse.

        Returns:
            PluginMetadata | None: the parsed metadata, or None.
        """
        try:
            with open(path) as metadataFile:
                content = json.load(metadataFile)
        except FileNotFoundError:
            logging.debug(f"No metadata file was found at '{path}'.")
            return None
        except json.JSONDecodeError as err:
            logging.error(f"Malformed JSON in the metadata file '{path}': {err}")
            return None
        except IOError as err:
            logging.error(f"Error while accessing the metadata file '{path}': {err}")
            return None

        if isinstance(content, list):
            return PluginMetadata(env=content)

        if not isinstance(content, dict):
            logging.warning(f"Metadata file '{path}' must contain a list or an object, "
                            f"got {type(content).__name__}. Ignoring it.")
            return None

        env = content.get("env", [])
        if not isinstance(env, list):
            logging.warning(f"'env' in metadata file '{path}' must be a list, "
                            f"got {type(env).__name__}. Ignoring it.")
            env = []

        return PluginMetadata(
            PluginMetadata._sanitizeName(content.get("name"), path),
            PluginMetadata._sanitizeVersion(content.get("version"), path),
            PluginMetadata._sanitizeEntity(content.get("publisher"), path),
            PluginMetadata._sanitizeAuthors(content.get("authors"), path),
            env
        )

    @staticmethod
    def loadToml(path: Path) -> Optional[PluginMetadata]:
        """
        Parse the "pyproject.toml" file at "path" into a PluginMetadata:
        - "name"/"version"/"authors" come from the standard "[project]" table.
        - "publisher"/"env" from the Meshroom-specific "[tool.meshroom]" table.

        Args:
            path: the absolute path of the pyproject.toml file to parse.

        Returns:
            PluginMetadata | None: the parsed metadata, or None.
        """
        try:
            with open(path, "rb") as tomlFile:
                content = tomllib.load(tomlFile)
        except FileNotFoundError:
            logging.debug(f"No pyproject.toml file was found at '{path}'.")
            return None
        except tomllib.TOMLDecodeError as err:
            logging.error(f"Malformed TOML in the metadata file '{path}': {err}")
            return None
        except IOError as err:
            logging.error(f"Error while accessing the metadata file '{path}': {err}")
            return None

        project = content.get("project", {})
        if not isinstance(project, dict):
            project = {}

        tool = content.get("tool", {})
        meshroom = tool.get("meshroom", {}) if isinstance(tool, dict) else {}
        if not isinstance(meshroom, dict):
            meshroom = {}

        # A "[project].authors" entry is a PEP 621 {name, email} table
        # Keep name or tolerate a plain string.
        authorEntries = project.get("authors", [])
        authors = []
        if isinstance(authorEntries, list):
            for entry in authorEntries:
                if isinstance(entry, str):
                    authors.append(entry)
                elif isinstance(entry, dict) and isinstance(entry.get("name"), str):
                    authors.append(entry["name"])

        env = meshroom.get("env", [])
        if not isinstance(env, list):
            logging.warning(f"'[tool.meshroom].env' in metadata file '{path}' must be a list, "
                            f"got {type(env).__name__}. Ignoring it.")
            env = []

        return PluginMetadata(
            PluginMetadata._sanitizeName(project.get("name"), path),
            PluginMetadata._sanitizeVersion(project.get("version"), path),
            PluginMetadata._sanitizeEntity(meshroom.get("publisher"), path),
            PluginMetadata._sanitizeAuthors(authors, path),
            env
        )

    @staticmethod
    def _sanitizeName(name, path: Path) -> Optional[str]:
        """
        Return "name" if it matches PEP 621's "[project].name" rule, None otherwise.
        """
        if name is None:
            return None
        if not isinstance(name, str) or not _PLUGIN_NAME_PATTERN.match(name):
            logging.warning(f"Invalid 'name' in metadata file '{path}': {name!r}.\n"
                            f"Plugin names must only contain letters, digits, '.', '_' and '-', "
                            f"and start/end with a letter or digit. Ignoring it.")
            return None
        return name

    @staticmethod
    def _sanitizeVersion(version, path: Path) -> Optional[str]:
        """
        Return "version" if it only contains letters, digits, dots and '+', None otherwise.
        """
        if version is None:
            return None
        if not isinstance(version, str) or not _PLUGIN_VERSION_PATTERN.match(version):
            logging.warning(f"Invalid 'version' in metadata file '{path}': {version!r}.\n"
                            f"Versions must only contain letters, digits, dots and '+'. Ignoring it.")
            return None
        return version

    @staticmethod
    def _sanitizeEntity(entity, path: Path) -> Optional[str]:
        """
        Return "entity" (the publisher) if it only contains letters, hyphen, underscore and
        digits.
        """
        if entity is None:
            return None
        if not isinstance(entity, str) or not _PLUGIN_PUBLISHER_PATTERN.match(entity):
            logging.warning(f"Invalid 'publisher' in metadata file '{path}': {entity!r}.\n"
                            f"Publisher must only contain letters, digits, hyphen, "
                            f"and underscore. Ignoring it.")
            return None
        return entity

    @staticmethod
    def _sanitizeAuthors(authors, path: Path) -> list[str]:
        """
        Return "authors" filtered down to its string entries, dropping anything else and
        logging a warning. "authors" itself must be a list, if it is not, it is ignored
        entirely.
        """
        if authors is None:
            return []
        if not isinstance(authors, list):
            logging.warning(f"'authors' in metadata file '{path}' must be a list, "
                            f"got {type(authors).__name__}. Ignoring it.")
            return []
        validAuthors = [author for author in authors if isinstance(author, str)]
        if len(validAuthors) != len(authors):
            logging.warning(f"Invalid entries in 'authors' in metadata file '{path}': {authors!r}.\n"
                            f"Author entries must be strings. Ignoring invalid ones.")
        return validAuthors

    def resolveEnv(self, basePath: Path) -> dict[str, str]:
        """
        Resolve "env" into a dictionary of environment variable names to values.

        Args:
            basePath: the folder to resolve against when entry value is not absolute.

        Returns:
            dict[str, str]: the resolved environment variables.
        """
        resolvedEnv: dict[str, str] = {}
        for entry in self.env:
            # An entry is expected to be formatted as follows:
            # { "key": "key_of_var", "type": "type_of_value", "value": "var_value" }
            # If "type" is not provided, it is assumed to be "string"
            k = entry.get("key", None)
            t = entry.get("type", None)
            val = entry.get("value", None)

            if not k or not val:
                logging.warning(f"Invalid entry in metadata file for {self.name}: {entry}.")
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

            resolvedEnv[k] = str(val)
        return resolvedEnv

    def writeLockfile(self, path: Path) -> None:
        """
        Write this metadata as JSON to "path", stamping "createdAt" with the current UTC time.

        Args:
            path: the absolute path to write the metadata file to.
        """
        content = json.dumps({
            "name": self.name,
            "version": self.version,
            "publisher": self.publisher,
            "authors": self.authors,
            "env": self.env,
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }, indent=4)
        atomicWriteFile(path, content)
