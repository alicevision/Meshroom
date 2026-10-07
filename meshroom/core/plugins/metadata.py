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
from pathlib import Path, PurePosixPath, PureWindowsPath
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

# Plugin asset sha256 pattern.
# SHA-256 pattern: 64 hexadecimal characters.
_PLUGIN_SHA256_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")


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
        description: a short description of the plugin (if provided and valid).
        requirements: a human-readable description of the plugin's runtime requirements
                      (if provided and valid).
        license: a human-readable description of the plugin's license (if provided and valid).
        env: the list of environment variable entries declared in the file (if provided and valid).
        assets: the list of external assets declared in the file (valid entries only).
    """
    def __init__(self, name: Optional[str] = None, version: Optional[str] = None,
                 publisher: Optional[str] = None, authors: Optional[list[str]] = None,
                 description: Optional[str] = None, requirements: Optional[str] = None,
                 license: Optional[str] = None, env: Optional[list[dict]] = None,
                 assets: Optional[list[PluginAsset]] = None):
        self.name = name
        self.version = version
        self.publisher = publisher
        self.authors = authors if authors is not None else []
        self.description = description
        self.requirements = requirements
        self.license = license
        self.env = env if env is not None else []
        self.assets = assets if assets is not None else []

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
            PluginMetadata._sanitizePublisher(content.get("publisher"), path),
            PluginMetadata._sanitizeAuthors(content.get("authors"), path),
            PluginMetadata._sanitizeText(content.get("description"), "description", path),
            PluginMetadata._sanitizeText(content.get("requirements"), "requirements", path),
            PluginMetadata._sanitizeText(content.get("license"), "license", path),
            env,
            PluginMetadata._sanitizeAssets(content.get("assets"), path)
        )

    @staticmethod
    def loadToml(path: Path) -> Optional[PluginMetadata]:
        """
        Parse the "pyproject.toml" file at "path" into a PluginMetadata:
        - "name"/"version"/"authors"/"description"/"license" come from the standard "[project]" table.
        - "publisher"/"env"/"requirements"/"assets" from the Meshroom-specific "[tool.meshroom]" table.

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
            PluginMetadata._sanitizePublisher(meshroom.get("publisher"), path),
            PluginMetadata._sanitizeAuthors(authors, path),
            PluginMetadata._sanitizeText(project.get("description"), "description", path),
            PluginMetadata._sanitizeText(meshroom.get("requirements"), "requirements", path),
            PluginMetadata._resolveLicense(project, path),
            env,
            PluginMetadata._sanitizeAssets(meshroom.get("assets"), path)
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
    def _sanitizePublisher(publisher, path: Path) -> Optional[str]:
        """
        Return "publisher" if it only contains letters, hyphen, underscore and digits.
        """
        if publisher is None:
            return None
        if not isinstance(publisher, str) or not _PLUGIN_PUBLISHER_PATTERN.match(publisher):
            logging.warning(f"Invalid 'publisher' in metadata file '{path}': {publisher!r}.\n"
                            f"Publisher must only contain letters, digits, hyphen, "
                            f"and underscore. Ignoring it.")
            return None
        return publisher

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

    @staticmethod
    def _sanitizeText(value, fieldName: str, path: Path) -> Optional[str]:
        """
        Return "value" if it is a string, None otherwise.
        """
        if value is None:
            return None
        if not isinstance(value, str):
            logging.warning(f"'{fieldName}' in metadata file '{path}' must be a string, "
                            f"got {type(value).__name__}. Ignoring it.")
            return None
        return value

    @staticmethod
    def _resolveLicense(project: dict, path: Path) -> Optional[str]:
        """
        Return a displayable license string from the "[project]" table of a pyproject.toml, made of
        the name of the license followed by its files, e.g. "MIT (see file(s): LICENSE)".

        The name is the first of these declarations naming a license:
        - "license" as a string: an SPDX expression (PEP 639).
        - "license" as a table with a "text" key (legacy PEP 621).
        - the "License ::" entries of "classifiers".
        The files are those of "license" as a table with a "file" key and of "license-files".

        Args:
            project: the "[project]" table of the pyproject.toml file.
            path: the absolute path of the pyproject.toml file.

        Returns:
            str | None: the license string, or None if no license is declared.
        """
        declared = project.get("license")
        name = None
        files = []
        if isinstance(declared, str):
            name = declared.strip()
        elif isinstance(declared, dict):
            text = declared.get("text")
            if isinstance(text, str):
                # A full license text may be pasted here: only keep its first non-empty line.
                lines = [line.strip() for line in text.splitlines() if line.strip()]
                name = lines[0] if lines else None
            if isinstance(declared.get("file"), str) and declared["file"]:
                files.append(PurePosixPath(declared["file"]).as_posix())
        elif declared is not None:
            logging.warning(f"'license' in metadata file '{path}' must be a string or a table, "
                            f"got {type(declared).__name__}. Ignoring it.")

        # Classifiers are only a fallback: they would repeat the name declared by "license".
        if not name:
            name = ", ".join(PluginMetadata._licensesFromClassifiers(project.get("classifiers")))

        files += PluginMetadata._resolveLicenseFiles(project.get("license-files"), path)
        # Remove duplicates, keeping the declaration order.
        files = list(dict.fromkeys(files))
        if not files:
            return name or None
        filesText = f"file(s): {', '.join(files)}"
        return f"{name} (see {filesText})" if name else f"See {filesText}"

    @staticmethod
    def _licensesFromClassifiers(classifiers) -> list[str]:
        """
        Return the license names declared by the "License ::" trove classifiers of "classifiers",
        e.g. "MIT License" for "License :: OSI Approved :: MIT License".
        """
        if not isinstance(classifiers, list):
            return []
        names = []
        for classifier in classifiers:
            if not isinstance(classifier, str):
                continue
            segments = [segment.strip() for segment in classifier.split("::")]
            if len(segments) < 2 or segments[0] != "License":
                continue
            name = segments[-1]
            # "License :: OSI Approved" is a category, it does not name a license.
            if name and name != "OSI Approved" and name not in names:
                names.append(name)
        return names

    @staticmethod
    def _resolveLicenseFiles(licenseFiles, path: Path) -> list[str]:
        """
        Return the files matching the "license-files" glob patterns of a pyproject.toml, relative to
        its folder (POSIX separators). A pattern matching no file is returned as written.

        Args:
            licenseFiles: the "[project].license-files" value: a list of glob patterns (PEP 639), or
                          a table with a "paths" or a "globs" list (draft form of PEP 639).
            path: the absolute path of the pyproject.toml file.

        Returns:
            list[str]: the license files.
        """
        if licenseFiles is None:
            return []
        patterns = licenseFiles
        if isinstance(licenseFiles, dict):
            patterns = licenseFiles.get("paths") or licenseFiles.get("globs") or []
        if not isinstance(patterns, list):
            logging.warning(f"'license-files' in metadata file '{path}' must be a list, "
                            f"got {type(licenseFiles).__name__}. Ignoring it.")
            return []

        folder = Path(path).parent
        files = []
        for pattern in patterns:
            if not isinstance(pattern, str) or not pattern:
                continue
            posixPattern = PurePosixPath(pattern)
            # Patterns must stay inside the plugin folder.
            if posixPattern.is_absolute() or PureWindowsPath(pattern).drive or ".." in posixPattern.parts:
                logging.warning(f"Invalid entry in 'license-files' in metadata file '{path}': {pattern!r}.\n"
                                f"Patterns must be relative, without '..'. Ignoring it.")
                continue
            try:
                matches = sorted(match.relative_to(folder).as_posix()
                                 for match in folder.glob(pattern) if match.is_file())
            except (ValueError, NotImplementedError, OSError):
                matches = []
            files += matches or [pattern]
        return files

    @staticmethod
    def _sanitizeAssets(assets, path: Path) -> list[PluginAsset]:
        """
        Return "assets" parsed into PluginAssets, dropping invalid entries and logging a warning.
        "assets" itself must be a list, if it is not, it is ignored entirely.

        Each entry is expected to be formatted as follows:
        { "name": "...", "category": "...", "url": "...", "path": "...", "sha256": "..." }
        "sha256" is optional.
        """
        if assets is None:
            return []
        if not isinstance(assets, list):
            logging.warning(f"'assets' in metadata file '{path}' must be a list, "
                            f"got {type(assets).__name__}. Ignoring it.")
            return []

        validAssets: list[PluginAsset] = []
        for entry in assets:
            asset = PluginMetadata._sanitizeAsset(entry, path)
            if asset is None:
                continue
            if any(asset.name == other.name for other in validAssets):
                logging.warning(f"Duplicate asset name '{asset.name}' in metadata file '{path}'. Ignoring it.")
                continue
            if any(asset.path == other.path for other in validAssets):
                logging.warning(f"Duplicate asset path '{asset.path}' in metadata file '{path}'. Ignoring it.")
                continue
            validAssets.append(asset)
        return validAssets

    @staticmethod
    def _sanitizeAsset(entry, path: Path) -> Optional[PluginAsset]:
        """
        Return the asset "entry" parsed into a PluginAsset, or None (logging a warning) if it is invalid.
        """
        def invalid(reason: str) -> None:
            logging.warning(f"Invalid entry in 'assets' in metadata file '{path}': {entry!r}.\n"
                            f"{reason} Ignoring it.")

        if not isinstance(entry, dict):
            return invalid("Asset entries must be tables/objects.")
        for key in ("name", "category", "url", "path"):
            if not isinstance(entry.get(key), str) or not entry[key]:
                return invalid(f"'{key}' must be a non-empty string.")

        name = entry["name"]
        if not _PLUGIN_NAME_PATTERN.match(name):
            return invalid("'name' must only contain letters, digits, '.', '_' and '-', "
                           "and start/end with a letter or digit.")

        assetPath = entry["path"]
        posixPath = PurePosixPath(assetPath)
        if (posixPath.is_absolute() or PureWindowsPath(assetPath).drive or "\\" in assetPath
                or ".." in posixPath.parts or not posixPath.parts):
            return invalid("'path' must be a relative path inside the plugin folder, without '..'.")

        sha256 = entry.get("sha256")
        if sha256 is not None:
            if not isinstance(sha256, str) or not _PLUGIN_SHA256_PATTERN.match(sha256):
                return invalid("'sha256' must be a string of 64 hexadecimal characters.")
            sha256 = sha256.lower()

        return PluginAsset(name, entry["category"], entry["url"], posixPath.as_posix(), sha256)

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
            "description": self.description,
            "requirements": self.requirements,
            "license": self.license,
            "env": self.env,
            "assets": [asset.toDict() for asset in self.assets],
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }, indent=4)
        atomicWriteFile(path, content)


class PluginAsset:
    """
    An external file (model, weights, data...) declared by a plugin, downloaded into the plugin folder
    when the plugin is installed.

    Members:
        name: the asset's name, unique within the plugin.
        category: a free-form label describing the kind of asset (e.g. "model", "weights", "data").
        url: the url to download the asset from.
        path: the file path of the asset, relative to the plugin folder (POSIX separators).
        sha256: the expected SHA-256 hexdigest of the asset (lowercase), or None if not provided.
    """
    def __init__(self, name: str, category: str, url: str, path: str, sha256: Optional[str] = None):
        self.name = name
        self.category = category
        self.url = url
        self.path = path
        self.sha256 = sha256

    def __eq__(self, other) -> bool:
        return isinstance(other, PluginAsset) and self.toDict() == other.toDict()

    def __repr__(self) -> str:
        return f"PluginAsset({self.toDict()!r})"

    def toDict(self) -> dict:
        return {
            "name": self.name,
            "category": self.category,
            "url": self.url,
            "path": self.path,
            "sha256": self.sha256,
        }

    def resolvePath(self, pluginFolder: Path) -> Path:
        """ Return the absolute path of the asset within "pluginFolder". """
        return Path(pluginFolder).joinpath(*PurePosixPath(self.path).parts)
