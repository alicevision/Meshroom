from __future__ import annotations

from typing import Optional

from meshroom.common import BaseObject, Property, VariantList


class PluginRecord(BaseObject):
    """
    A plugin View Model describing an unloaded / external plugin that is not (yet) installed.
    """
    def __init__(self, name: str, version: str, publisher: str, url: str,
                 description: Optional[str] = None, versions: Optional[list[str]] = None,
                 authors: Optional[list[str]] = None, requirements: Optional[str] = None,
                 parent: BaseObject = None):
        super().__init__(parent)
        self._name = name
        self._version = version
        self._publisher = publisher
        self._url = url
        self._description = description
        self._versions = versions if versions is not None else []
        self._authors = authors if authors is not None else []
        self._requirements = requirements

    # The name of the plugin.
    name = Property(str, lambda self: self._name, constant=True)
    # The version of the plugin.
    version = Property(str, lambda self: self._version, constant=True)
    # The publisher of the plugin.
    publisher = Property(str, lambda self: self._publisher, constant=True)
    # The URL the plugin can be downloaded/installed from.
    url = Property(str, lambda self: self._url, constant=True)
    # A short description of the plugin.
    description = Property(str, lambda self: self._description, constant=True)
    # The list of versions available for the plugin.
    versions = Property(VariantList, lambda self: self._versions, constant=True)
    # The list of the plugin's authors.
    authors = Property(VariantList, lambda self: self._authors, constant=True)
    # A human-readable description of the plugin's runtime requirements.
    requirements = Property(str, lambda self: self._requirements, constant=True)
