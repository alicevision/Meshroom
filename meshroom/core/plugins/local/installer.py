from __future__ import annotations

import io
import logging
import os
import shutil
import zipfile

from typing import Optional
from pathlib import Path

from meshroom.env import EnvVar
from meshroom.core.files import scratchFolder
from meshroom.core.httpUtils import RequestError, fetchWithProgress
from meshroom.core.plugins import meshroomPluginsFolder, meshroomPluginsInternalPrefix
from meshroom.core.plugins.metadata import PluginMetadata
from meshroom.core.plugins.record import PluginRecord
from meshroom.core.plugins.provider import PluginProvider
from meshroom.core.plugins.local.service import PluginService
from meshroom.core.plugins.local.uv import findUv, pythonForUv, parseUvProgress, runUv, runUvWithProgress

# The overall progress (from 0 to 1) once the plugin archive is downloaded.
_INSTALL_PROGRESS_DOWNLOAD = 0.4
# The overall progress (from 0 to 1) once the plugin archive is extracted.
_INSTALL_PROGRESS_EXTRACT = 0.5
# The number of bytes downloaded at which the progress of a download of unknown size reaches half its range.
_INSTALL_SIZE_SCALE = 5 * 1024 * 1024


def downloadProgress(bytesRead: int, totalBytes: int) -> float:
    """
    Return the overall progress (from 0 to _INSTALL_PROGRESS_DOWNLOAD) of a download.

    When "totalBytes" is unknown (<= 0, e.g. GitHub archives are streamed without a "Content-Length"),
    the progress creeps toward (without reaching) _INSTALL_PROGRESS_DOWNLOAD so it does not look stuck:
    half the range at "_INSTALL_SIZE_SCALE" bytes, closer and closer to it as more bytes come in.
    """
    if totalBytes > 0:
        return _INSTALL_PROGRESS_DOWNLOAD * min(bytesRead / totalBytes, 1.0)
    return _INSTALL_PROGRESS_DOWNLOAD * bytesRead / (bytesRead + _INSTALL_SIZE_SCALE)


class PluginInstaller(PluginService):
    """
    Installs a plugin from its PluginProvider into "<pluginsPath>/<pluginName>":
        1. Download the plugin archive.
        2. Extract it, and generate its "plugin.lock".
        3. Install its Python dependencies with "uv" into "<pluginFolder>/venv".

    A plugin is only installed once all of this is done: if the installation fails or is cancelled
    after the plugin folder has been created, that folder is removed.
    """

    def __init__(self, provider: PluginProvider, record: PluginRecord,
                 version: Optional[str] = None, pluginsPath: Path = meshroomPluginsFolder) -> None:
        """
        Args:
            provider: the PluginProvider to download the plugin from.
            record: the record describing the plugin to install.
            version: the version to install, or the version of "record" if None.
            pluginsPath: the folder to install the plugin in.
        """
        super().__init__("installation", record.name, Path(pluginsPath))
        self._provider: PluginProvider = provider
        self._record: PluginRecord = record
        self._version: str = version or record.version

    def _run(self) -> None:
        """
        Install the plugin: download it, extract it, then install its dependencies.
        """
        if not EnvVar.get(EnvVar.MESHROOM_LOCAL_PLUGINS):
            raise self._error("Verification", "Local plugin management is disabled.")

        # Check the plugin is not installed yet.
        pluginFolder = self._pluginsPath / self._record.name
        if pluginFolder.exists():
            raise self._error("Verification", f"Plugin is already installed in '{pluginFolder}'.")

        # Download the plugin archive.
        self._reportProgress("Downloading", 0.0)
        content = self._download()

        # Extract the plugin archive / metadata in plugins folder.
        self._reportProgress("Extracting", _INSTALL_PROGRESS_DOWNLOAD)
        pluginFolder = self._extract(content)

        # Install the plugin's dependencies.
        self._reportProgress("Installing dependencies", _INSTALL_PROGRESS_EXTRACT)
        try:
            self._installDependencies(pluginFolder)
        except BaseException:
            # Do not leave a half-installed plugin behind.
            shutil.rmtree(pluginFolder, ignore_errors=True)
            raise

        self._reportProgress("Plugin installed", 1.0)
        logging.info(f"Plugin '{self._record.name}' installed in '{pluginFolder}'")

    def _download(self) -> bytes:
        """
        Download the plugin archive from the provider, reporting the progress of the download.

        Returns:
            bytes: the content of the plugin archive.
        """
        # Check if the user canceled the service.
        self._checkCancel()
        # Get archive url.
        archiveUrl = self._provider.archiveUrl(self._version)
        logging.info(f"Downloading plugin '{self._record.name}' from '{archiveUrl}'...")

        def onBytes(bytesRead: int, totalBytes: int) -> None:
            # Raising from here aborts the download.
            self._checkCancel()
            # Without a known total size, show the downloaded size instead of a percentage.
            message = "Downloading" if totalBytes > 0 else f"Downloading ({bytesRead / 1e6:.1f} MB)"
            self._reportProgress(message, downloadProgress(bytesRead, totalBytes))

        try:
            return fetchWithProgress(archiveUrl, onBytes=onBytes)
        except RequestError as exc:
            raise self._error("Download", f"Failed to download '{archiveUrl}'.", exc)

    def _extract(self, content: bytes) -> Path:
        """
        Extract the downloaded archive and move the plugin to "<pluginsPath>/<pluginName>", together
        with the "plugin.lock" generated from its metadata.

        Args:
            content: the content of the plugin archive.

        Returns:
            Path: the plugin folder.
        """
        # Check if the user canceled the service.
        self._checkCancel()
        # Extract the archive in a scratch folder next to the plugins folder, so moving the result
        # into place below is a same-filesystem, truly atomic rename.
        with scratchFolder(self._pluginsPath, prefix=meshroomPluginsInternalPrefix) as tmpDir:
            try:
                extractedRoot = self._unzipArchive(content, tmpDir)
            except (ValueError, zipfile.BadZipFile, OSError) as exc:
                raise self._error("Extraction", "Invalid plugin archive.", exc)

            # The name of the plugin folder comes from the plugin's metadata, not from the record.
            metadata = self._loadMetadata(extractedRoot)
            pluginFolder = self._pluginsPath / metadata.name
            if pluginFolder.exists():
                raise self._error("Extraction", f"Plugin '{metadata.name}' is already installed in '{pluginFolder}'.")

            # Generate the "plugin.lock" and move the plugin into the plugins folder.
            metadata.writeLockfile(extractedRoot / "plugin.lock")
            try:
                os.rename(extractedRoot, pluginFolder)
            except OSError as exc:
                raise self._error("Extraction", f"Failed to move the plugin to '{pluginFolder}'.", exc)

        logging.info(f"Plugin '{self._record.name}' extracted in '{pluginFolder}'")
        return pluginFolder

    def _unzipArchive(self, content: bytes, destination: Path) -> Path:
        """
        Extract the zip archive "content" into the existing folder "destination".

        Args:
            content: the bytes of the zip archive. It must contain a single root folder.
            destination: the existing folder to extract into.

        Returns:
            Path: the extracted root folder of the plugin, "destination/<archive root folder>".
        """
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            names = archive.namelist()
            if any(".." in name.split("/") for name in names):
                raise ValueError("Unsafe path in archive.")

            rootFolders = {name.split("/")[0] for name in names}
            if len(rootFolders) != 1:
                raise ValueError("Unexpected archive layout: expected a single root folder.")

            archive.extractall(destination)
        return Path(destination) / rootFolders.pop()

    def _loadMetadata(self, pluginRoot: Path) -> PluginMetadata:
        """
        Load the metadata of the plugin extracted in "pluginRoot".

        Each source is tried in order, the first match is kept:
        1. "pyproject.toml" (standard project metadata).
        2. "meshroom/config.json" (legacy support).
        If none of them provides metadata, fall back to an empty one. Whatever the metadata is missing
        (name, version, publisher) is then resolved from the plugin record.

        Args:
            pluginRoot: the root folder of the extracted plugin.

        Returns:
            PluginMetadata: the metadata of the plugin.
        """
        metadata = PluginMetadata.loadToml(pluginRoot / "pyproject.toml")
        if metadata is None:
            metadata = PluginMetadata.loadJson(pluginRoot / "meshroom" / "config.json")
        if metadata is None:
            metadata = PluginMetadata()
        if not metadata.name:
            metadata.name = self._record.name
        if not metadata.version:
            metadata.version = self._record.version
        if not metadata.publisher:
            metadata.publisher = self._record.publisher
        return metadata

    def _installDependencies(self, pluginFolder: Path) -> None:
        """
        Install the plugin's Python dependencies into "<pluginFolder>/venv": with "uv sync" when it
        ships a "pyproject.toml", otherwise with "uv pip install" from its "requirements.txt".
        A plugin without any of these files simply has no dependencies, which is not an error.

        Args:
            pluginFolder: the folder of the plugin.
        """
        # Check if the user canceled the service.
        self._checkCancel()

        pyprojectFile = pluginFolder / "pyproject.toml"
        requirementsFile = pluginFolder / "requirements.txt"
        venvFolder = pluginFolder / "venv"

        if not pyprojectFile.is_file() and not requirementsFile.is_file():
            logging.warning(f"No 'pyproject.toml' or 'requirements.txt' found for plugin at '{pluginFolder}'.")
            return

        # Find the "uv" executable, and the Python to build the environment with.
        uv = findUv()
        if not uv:
            raise self._error("Dependencies", "'uv' executable not found. Install uv (https://docs.astral.sh/uv/) "
                                              "or set the MESHROOM_UV_PATH environment variable.")
        python = pythonForUv()

        if pyprojectFile.is_file():
            # "uv sync" resolves against the plugin's "pyproject.toml"/"[tool.uv]" and
            # creates the target environment itself.
            # "--no-install-project" installs only the dependencies.
            # "--no-default-groups" skips dev groups.
            # "--frozen" reuses an existing "uv.lock" without re-resolving.
            # "uv sync" has no flag to point at an env outside "<project>/.venv": the
            # "UV_PROJECT_ENVIRONMENT" variable is the only way to redirect it to "venv".
            args = ["sync", "--python", python, "--project", str(pluginFolder),
                    "--no-install-project", "--no-default-groups"]
            if (pluginFolder / "uv.lock").is_file():
                args.append("--frozen")
            self._runUv(uv, args, env={"UV_PROJECT_ENVIRONMENT": str(venvFolder)})
        else:
            # "uv pip" installs into an existing environment, so create "venv" first,
            # then target it with "--python <dir>".
            if not venvFolder.is_dir():
                self._runUv(uv, ["venv", "--python", python, str(venvFolder)])
            self._runUv(uv, ["pip", "install", "--python", str(venvFolder), "-r", str(requirementsFile)])

    def _runUv(self, uv: str, args: list[str], env: Optional[dict] = None) -> None:
        """
        Run the "uv" executable with "args". If a progress callback is set, each line of its output
        is logged and reported as it streams. Otherwise the command is simply run to completion.

        Args:
            uv: the path of the "uv" executable.
            args: the arguments of the "uv" command.
            env: the environment variables to set for the command, on top of the current environment.
        """
        cmd = [uv, *args]
        progress = 0.0
        output: list[str] = []

        def onLine(line: str) -> None:
            nonlocal progress
            self._checkCancel()
            # "progress" is the progress of this command
            #  Map it to the dependencies part of the overall progress.
            progress = parseUvProgress(line, progress)
            self._reportProgress("Installing dependencies",
                                 _INSTALL_PROGRESS_EXTRACT + (1 - _INSTALL_PROGRESS_EXTRACT) * progress)

        try:
            if self._onProgress is not None:
                returnCode = runUvWithProgress(cmd, onLine, env, output)
            else:
                self._checkCancel()
                returnCode = runUv(cmd, env)
        except OSError as exc:
            raise self._error("Dependencies", f"Failed to launch '{' '.join(cmd)}'.", exc)
        if returnCode != 0:
            if output:
                logging.error(f"UV command failed (exit code {returnCode}): {' '.join(cmd)}\n" + "\n".join(output))
            raise self._error("Dependencies", f"UV command failed (exit code {returnCode})")
