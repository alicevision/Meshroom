from __future__ import annotations

import logging
import re

from abc import ABC, abstractmethod
from typing import Optional

from meshroom.core.httpUtils import fetchStatus
from meshroom.core.plugins.record import PluginRecord


def getPluginProviderFromUrl(url: str) -> Optional[PluginProvider]:
    """
    Return a PluginProvider instance bound to "url".

    Args:
        url: the url of a plugin source.

    Returns:
        PluginProvider | None: the matching PluginProvider instance, or None.
    """
    for providerClass in (GithubPluginProvider, ArchivePluginProvider):
        provider = providerClass.fromUrl(url)
        if provider:
            return provider
    logging.warning(f"Unable to get plugin provider from '{url}'.")
    return None


class PluginProvider(ABC):
    """A PluginProvider represents where one specific plugin's downloadable code comes from."""

    @classmethod
    @abstractmethod
    def fromUrl(cls, url: str) -> Optional[PluginProvider]:
        """ Return an instance bound to "url", or None if this provider type does not recognize it. """
        raise NotImplementedError

    @abstractmethod
    def archiveUrl(self, version: str) -> Optional[str]:
        """ The url of the downloadable archive for "version" of this provider's plugin. """
        raise NotImplementedError

    @abstractmethod
    def completeRecord(self, pluginRecord: PluginRecord) -> Optional[PluginRecord]:
        """ Validate/complete a PluginRecord parsed from a registry file entry. """
        raise NotImplementedError

    def isVersionAvailable(self, version: str) -> bool:
        """
        Check whether "version" exists as a downloadable archive of this provider's plugin, without
        downloading it.

        Args:
            version: the version (a tag/branch name, or "<branch>+<commit>") to check.

        Returns:
            bool: True if an archive for "version" is reachable, False otherwise.
        """
        archiveUrl = self.archiveUrl(version)
        if not archiveUrl:
            return False
        status = fetchStatus(archiveUrl, method="HEAD")
        if status is None or status >= 400:
            if status is not None:
                logging.warning(f"Failed to check availability of '{archiveUrl}': HTTP {status}")
            return False
        return True


class GithubPluginProvider(PluginProvider):
    """PluginProvider implementation for plugins hosted on GitHub."""
    def __init__(self, publisher: str, repo: str):
        self.publisher = publisher
        self.repo = repo

    # Override
    @classmethod
    def fromUrl(cls, url: str) -> Optional[GithubPluginProvider]:
        """
        Parse "url" as a strict "https://github.com/<publisher>/<repo>" GitHub repository url and
        return a GithubPluginProvider bound to it, or None if "url" does not match.
        """
        match = re.match(r"^https://(?:www\.)?github\.com/(?P<publisher>[\w-]+)/(?P<repo>[\w.-]+)/?$", url)
        if not match:
            return None
        return cls(match.group("publisher"), match.group("repo"))

    # Override
    def archiveUrl(self, version: str) -> Optional[str]:
        """ The url of the downloadable zip archive for "version" (a tag/branch/commit ref) of this repository. """
        ref = version.split("+")[-1] if "+" in version else version
        return f"https://github.com/{self.publisher}/{self.repo}/archive/{ref}.zip"

    # Override
    def completeRecord(self, pluginRecord: PluginRecord) -> Optional[PluginRecord]:
        """ Validate/complete a PluginRecord parsed from a registry file entry. """
        if not pluginRecord.version:
            return None

        if pluginRecord.name and pluginRecord.publisher:
            return pluginRecord

        name = pluginRecord.name or self.repo
        publisher = pluginRecord.publisher or self.publisher

        return PluginRecord(name=name, version=pluginRecord.version, publisher=publisher, url=pluginRecord.url,
                            description=pluginRecord.description, versions=pluginRecord.versions,
                            authors=pluginRecord.authors, requirements=pluginRecord.requirements,
                            parent=pluginRecord.parent())


class ArchivePluginProvider(PluginProvider):
    """PluginProvider implementation for plugins from an archive url. """
    def __init__(self, url: str):
        self.url = url

    # Override
    @classmethod
    def fromUrl(cls, url: str) -> Optional[ArchivePluginProvider]:
        """ Accept any url ending in ".zip" as a direct archive url, or None otherwise. """
        if not url.lower().endswith(".zip"):
            return None
        return cls(url)

    # Override
    def archiveUrl(self, version: str) -> Optional[str]:
        """ This provider's own url, it already points directly at the archive. """
        return self.url

    # Override
    def completeRecord(self, pluginRecord: PluginRecord) -> Optional[PluginRecord]:
        """ Validate/complete a PluginRecord parsed from a registry file entry. """
        if not pluginRecord.name:
            return None
        return pluginRecord
