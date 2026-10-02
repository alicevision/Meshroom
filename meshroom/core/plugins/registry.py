from __future__ import annotations

import json
import logging
import time

from pathlib import Path
from typing import Optional

from meshroom.common import BaseObject, Property, Signal, VariantList
from meshroom.core.files import atomicWriteFile
from meshroom.core.httpUtils import RequestError, etagMatch, fetchWithETag
from meshroom.core.plugins import isValidPluginName, meshroomPluginsInternalPrefix
from meshroom.core.plugins.record import PluginRecord
from meshroom.core.plugins.provider import getPluginProviderFromUrl

# How long a local registry copy is trusted without re-validating it against its remote source.
_REGISTRY_TTL_SECONDS = 72 * 60 * 60  # 3 days


class PluginRegistry(BaseObject):
    """
    A PluginRegistry represents one url that publishes a list of many downloadable plugins.
    It holds the PluginRecords parsed from its local registry file in a dictionary {name: PluginRecord}.
    A registry file is a single JSON document (a JSON object), shaped as follows:

        {
            "name": "My Registry",
            "description": "My Meshroom plugin registry",
            "url": "https://...path/to/my/project/page",
            "fileUrl": "https://...path/to/my/registry/myRegistry.json",
            "entries": [
                {
                    "name": "MyPlugin",
                    "url": "https://github.com/publisher/repo",
                    "versions": ["1.2", "1.1"],
                    "publisher": "myRegistry",
                    "description": "What the plugin does",
                    "authors": ["Jane Doe"],
                    "requirements": ["..."]
                },
                ...
            ]
        }

    Top-level fields:
        - "name": displayable name for the registry itself.
        - "description": description of what the registry publishes.
        - "url": an optional homepage/info url for the registry.
        - "fileUrl": the url this very document can itself be (re-)fetched from.
        - "entries": the list of plugin entries, each describing one downloadable plugin.

    Entry fields:
        - "url": where the plugin comes from, understood by a PluginProvider.
        - "name": name of the plugin.
        - "publisher": publisher of the plugin.
        - "versions": available versions, newest first (a single "version" string is also accepted).
        - "description", "authors", "requirements": optional plugin metadata.
    """

    def __init__(self, path: Path, parent: BaseObject = None):
        super().__init__(parent)
        self._name = path.stem
        self._path = path
        self._etagPath = path.with_name(f"{path.name}.etag")
        self._records: dict[str, PluginRecord] = {}  # {name: PluginRecord}

    # Signals
    recordsChanged = Signal()

    # Properties
    name = Property(str, lambda self: self._name, constant=True)
    path = Property(str, lambda self: str(self._path), constant=True)
    records = Property(VariantList, lambda self: list(self._records.values()), notify=recordsChanged)

    def getRecord(self, name: str) -> Optional[PluginRecord]:
        """
        Return the PluginRecord registered under "name" in this registry, if any.

        Args:
            name: the name of the plugin record to look up.

        Returns:
            PluginRecord | None: the matching record, or None.
        """
        return self._records.get(name)

    def matchesRemote(self, useTTL: bool = True) -> bool:
        """
        Check whether the local registry file is already up to date with its remote source,
        without downloading its content. Skipped entirely (assumed up to date) if "useTTL" is
        set and it was last checked less than _REGISTRY_TTL_SECONDS ago. Otherwise checked
        using the ETag stored alongside it.

        Args:
            useTTL: if True, skip re-validation as long as the TTL has not expired.

        Returns:
            bool: True if the local registry file is still considered up to date.
        """
        # Get JSON dict registry.
        registry = self._getRegistry()
        if registry is None:
            return False

        # Get registry file url.
        registryUrl = self._getRegistryUrl(registry)
        if not registryUrl:
            return False

        # Get timestamp and ETag.
        try:
            with open(self._etagPath, "r") as f:
                timestamp, _, etag = f.read().partition("\n")
        except OSError:
            return False

        try:
            timestamp = float(timestamp)
        except ValueError:
            return False

        if useTTL and (time.time() - timestamp) < _REGISTRY_TTL_SECONDS:
            return True

        etag = etag.strip()
        if not etag:
            return False

        return etagMatch(registryUrl, etag)

    def fetch(self, url: Optional[str] = None) -> Optional[Path]:
        """
        Unconditionally download the registry file, save it together with its ETag and the
        current time, so a later matchesRemote() call can use them.

        Args:
            url: the url to download the registry file from. If not given, read from this
                 registry's own local file (a refresh): its "fileUrl" field.

        Returns:
            Path | None: The local path of the registry file, or None.
        """
        registryUrl = url
        if registryUrl is None:
            # Get JSON dict registry.
            registry = self._getRegistry()
            if registry is None:
                return None

            # Get registry file url.
            registryUrl = self._getRegistryUrl(registry)
            if not registryUrl:
                return None

        try:
            content, etag = fetchWithETag(registryUrl)
        except RequestError as exc:
            logging.warning(f"Failed to download remote registry file '{registryUrl}':\n"
                            f"{exc}")
            return None

        try:
            document = json.loads(content)
        except json.JSONDecodeError:
            logging.warning(f"Failed to decode remote registry file '{registryUrl}':\n"
                            f"Not a valid JSON file.")
            return None
        if not isinstance(document, dict):
            logging.warning(f"Registry '{registryUrl}' does not contain a registry document.")
            return None

        # Write registry file.
        # Temporary "prefix" to meshroomPluginsInternalPrefix (scratch).
        try:
            atomicWriteFile(self._path, content, mode="wb", prefix=meshroomPluginsInternalPrefix)
        except OSError as exc:
            logging.warning(f"Cannot write registry file '{self._path}':\n{exc}")
            return None

        # Write Etag file.
        # Temporary "prefix" to meshroomPluginsInternalPrefix (scratch).
        try:
            atomicWriteFile(self._etagPath, f"{time.time()}\n{etag or ''}", prefix=meshroomPluginsInternalPrefix)
        except OSError as exc:
            logging.warning(f"Cannot write registry file etag '{self._etagPath}':\n{exc}")

        return self._path

    def updateRecords(self) -> bool:
        """
        Refresh the stored records from the registry's file.

        Returns:
            bool: whether the records were successfully updated.
        """
        updated = self._loadRecords()
        self.recordsChanged.emit()
        return updated

    def _getRegistry(self) -> Optional[dict]:
        """
        Load the registry's file as a JSON object.

        Returns:
            dict | None: the parsed registry document, or None.
        """
        try:
            with open(self._path, "r") as f:
                registry = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            logging.warning(f"Unable to load plugin registry from '{self._path}':\n{exc}")
            return None
        if not isinstance(registry, dict):
            logging.warning(f"Cannot read registry file '{self._path}'.")
            return None
        return registry

    def _getRegistryUrl(self, registry: dict) -> Optional[str]:
        """
        Get the URL of the remote registry file from the registry's document.

        Args:
            registry: the parsed registry document, as returned by _getRegistry().

        Returns:
            str | None: the value of "fileUrl", or None.
        """
        fileUrl = registry.get("fileUrl")
        if not isinstance(fileUrl, str) or not fileUrl:
            logging.info(f"Unable to get plugin registry source from '{self._path}':\n"
                         f"Missing or invalid 'fileUrl' in registry metadata.")
            return None
        return fileUrl

    def _loadRecords(self) -> bool:
        """
        Parse the registry's file into PluginRecords, completing/validating each entry against
        the PluginProvider that published it, and store them by name.

        Returns:
            bool: whether the file was valid and its records stored.
        """
        self._records = {}

        # Get JSON dict registry.
        registry = self._getRegistry()
        if registry is None:
            return False

        entries = registry.get("entries")
        if not isinstance(entries, list):
            logging.warning(f"Registry file '{self._path}' does not contain an 'entries' list.")
            return False

        records: dict[str, PluginRecord] = {}
        for entry in entries:
            # A single invalid entry invalidates the whole registry.
            if not isinstance(entry, dict):
                logging.warning(f"Invalid entry in registry file '{self._path}': not a JSON object.")
                return False
            url = entry.get("url", "")
            versions = entry.get("versions") or []
            if not isinstance(url, str) or not isinstance(versions, list):
                logging.warning(f"Invalid entry in registry file '{self._path}': "
                                f"'url' must be a string and 'versions' a list.")
                return False
            entryProvider = getPluginProviderFromUrl(url)
            if not entryProvider:
                logging.warning(f"Invalid entry in registry file '{self._path}': unsupported plugin source '{url}'.")
                return False
            version = versions[0] if versions else entry.get("version", "")
            pluginRecord = PluginRecord(name=entry.get("name", ""), version=version,
                                        publisher=entry.get("publisher", ""), url=url,
                                        description=entry.get("description"), versions=versions,
                                        authors=entry.get("authors") or [],
                                        requirements=entry.get("requirements"),
                                        parent=self.parent())
            pluginRecord = entryProvider.completeRecord(pluginRecord)
            if not pluginRecord:
                logging.warning(f"Invalid entry '{url}' in registry file '{self._path}': incomplete plugin record.")
                return False
            # Plugin name is used as a folder name.
            name = pluginRecord.name
            if not isValidPluginName(name):
                logging.warning(f"Invalid entry '{url}' in registry file '{self._path}': invalid plugin name '{name}'.")
                return False
            if name in records:
                logging.warning(f"Duplicate plugin '{name}' in registry file '{self._path}', keeping the first one.")
                continue
            records[name] = pluginRecord
        self._records = records
        return True
