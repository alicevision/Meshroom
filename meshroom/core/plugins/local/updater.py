from __future__ import annotations

import logging

from typing import Optional
from pathlib import Path

from meshroom.env import EnvVar
from meshroom.core.plugins import isValidPluginName, meshroomPluginsFolder, meshroomPluginsInternalPrefix
from meshroom.core.plugins.record import PluginRecord
from meshroom.core.plugins.provider import PluginProvider
from meshroom.core.plugins.local.service import PluginService
from meshroom.core.plugins.local.installer import PluginInstaller
from meshroom.core.plugins.local.uninstaller import PluginUninstaller


class PluginUpdater(PluginService):
    """
    Updates a local plugin by installing a new version of it in place of the installed one:
        1. Move the installed plugin aside, to "<pluginsPath>/<internalPrefix><pluginName>".
        2. Install the new version with a PluginInstaller.
        3. Remove the moved plugin with a PluginUninstaller.

    If the installation fails or is cancelled, the installed plugin is moved back to its place.
    """

    def __init__(self, provider: PluginProvider, record: PluginRecord,
                 version: Optional[str] = None, pluginsPath: Path = meshroomPluginsFolder) -> None:
        """
        Args:
            provider: the PluginProvider to download the new version of the plugin from.
            record: the record describing the plugin to update.
            version: the version to install, or the version of "record" if None.
            pluginsPath: the folder the plugin is installed in.
        """
        super().__init__("update", record.name, Path(pluginsPath))
        self._installer: PluginInstaller = PluginInstaller(provider, record, version, self._pluginsPath)
        self._backupName: str = f"{meshroomPluginsInternalPrefix}{record.name}"

    def _run(self) -> None:
        """
        Update the plugin: move it aside, install its new version, then remove the moved plugin.
        """
        if not EnvVar.get(EnvVar.MESHROOM_LOCAL_PLUGINS):
            raise self._error("Verification", "Local plugin management is disabled.")

        # Check the name is a plain folder name, as the folder to move must be inside of "pluginsPath".
        if not isValidPluginName(self._pluginName):
            raise self._error("Verification", f"Invalid plugin name '{self._pluginName}'.")

        # Check the plugin is installed.
        pluginFolder = self._requireInstalledFolder()

        # Remove the backup a previous update may have left behind.
        backupFolder = self._pluginsPath / self._backupName
        if backupFolder.exists():
            self._removeBackup()

        # Check if the user canceled the service.
        self._checkCancel()

        # Move the installed plugin aside: this frees its folder for the installer.
        # A rename keeps the plugin's environment ("venv") usable when it is moved back.
        self._reportProgress("Backing up the installed plugin", 0.0)
        try:
            pluginFolder.rename(backupFolder)
        except OSError as exc:
            raise self._error("Backup", f"Failed to move '{pluginFolder}' to '{backupFolder}'.", exc)

        try:
            # The removal of the backup is fast, the progress is the one of the installer.
            self._installer.execute(self._reportProgress, self._isCancelled)
        except BaseException:
            # The installer removes what it has installed, put the previous version back.
            self._restoreBackup(pluginFolder, backupFolder)
            raise

        # The update is done, failing to remove the backup is not an error.
        self._reportProgress("Removing the previous version", 1.0)
        try:
            self._removeBackup()
        except Exception as exc:
            logging.warning(f"Plugin '{self._pluginName}' updated, but its backup '{backupFolder}' "
                            f"could not be removed: {exc}")

        self._reportProgress("Plugin updated", 1.0)
        logging.info(f"Plugin '{self._pluginName}' updated in '{pluginFolder}'")

    def _removeBackup(self) -> None:
        """ Remove the backup folder of the plugin, with a PluginUninstaller. """
        PluginUninstaller(self._backupName, self._pluginsPath).execute()

    def _restoreBackup(self, pluginFolder: Path, backupFolder: Path) -> None:
        """
        Move the backup folder back to the plugin folder.

        Args:
            pluginFolder: the folder of the plugin.
            backupFolder: the folder the installed plugin has been moved to.
        """
        try:
            backupFolder.rename(pluginFolder)
        except OSError as exc:
            logging.error(f"Failed to restore plugin '{self._pluginName}': move '{backupFolder}' back to '{pluginFolder}' "
                          f"manually. ({exc})")
