from __future__ import annotations

import logging
import shutil

from pathlib import Path

from meshroom.env import EnvVar
from meshroom.core.files import isSafeFolderName
from meshroom.core.plugins import meshroomPluginsFolder
from meshroom.core.plugins.local.service import PluginService


class PluginUninstaller(PluginService):
    """
    Uninstalls a local Meshroom plugin by removing its entire folder, "<pluginsPath>/<pluginName>".
    """

    def __init__(self, pluginName: str, pluginsPath: Path = meshroomPluginsFolder) -> None:
        """
        Args:
            pluginName: the name of the plugin to uninstall.
            pluginsPath: the folder the plugin is installed in.
        """
        super().__init__("uninstallation", pluginName, Path(pluginsPath))

    def _run(self) -> None:
        """ Uninstall the plugin: remove its folder. """
        if not EnvVar.get(EnvVar.MESHROOM_LOCAL_PLUGINS):
            raise self._error("Verification", "Local plugin management is disabled.")

        # Check the name is a plain folder name.
        if not isSafeFolderName(self._pluginName):
            raise self._error("Verification", f"Invalid plugin name '{self._pluginName}'.")

        # Check the plugin is installed.
        pluginFolder = self._requireInstalledFolder()

        # Check if the user canceled the service.
        self._checkCancel()

        # Remove the plugin folder.
        logging.info(f"Uninstall plugin '{self._pluginName}'")
        self._reportProgress("Removing plugin", 0.0)
        try:
            shutil.rmtree(pluginFolder)
        except OSError as exc:
            raise self._error("Removal", f"Failed to remove plugin folder '{pluginFolder}'.", exc)
        self._reportProgress("Plugin removed", 1.0)
