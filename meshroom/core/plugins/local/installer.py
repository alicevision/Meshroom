import io
import logging
import os
import shutil
import tarfile
import zipfile

from typing import Callable, Dict, List, Optional, Tuple
from pathlib import Path, PurePosixPath

from meshroom.env import EnvVar
from meshroom.core.files import scratchFolder
from meshroom.core.httpUtils import RequestError, fetchToFile, fetchWithProgress
from meshroom.core.plugins import meshroomPluginsFolder, meshroomPluginsInternalPrefix
from meshroom.core.plugins.metadata import PluginAsset, PluginInstalledAsset, PluginMetadata
from meshroom.core.plugins.record import PluginRecord
from meshroom.core.plugins.provider import PluginProvider
from meshroom.core.plugins.local.archives import extractArchive, isArchive, makeExecutable
from meshroom.core.plugins.local.releases import ReleaseError, currentPlatform, fetchReleaseFiles, selectReleaseFile
from meshroom.core.plugins.local.service import PluginService
from meshroom.core.plugins.local.uv import findUv, pythonForUv, parseUvProgress, runUv, runUvWithProgress

# The overall progress (from 0 to 1) once the plugin archive is downloaded.
_INSTALL_PROGRESS_DOWNLOAD = 0.4
# The overall progress (from 0 to 1) once the plugin archive is extracted.
_INSTALL_PROGRESS_EXTRACT = 0.5
# The overall progress (from 0 to 1) once the plugin dependencies are installed.
_INSTALL_PROGRESS_DEPENDENCIES = 0.9
# The number of bytes downloaded at which the progress of a download of unknown size reaches half its range.
_INSTALL_SIZE_SCALE = 5 * 1024 * 1024


def downloadProgress(bytesRead: int, totalBytes: int, start: float = 0.0,
                     end: float = _INSTALL_PROGRESS_DOWNLOAD) -> float:
    """
    Return the overall progress (from "start" to "end") of a download.

    When "totalBytes" is unknown (<= 0, e.g. GitHub archives are streamed without a "Content-Length"),
    the progress creeps toward (without reaching) "end" so it does not look stuck:
    half the range at "_INSTALL_SIZE_SCALE" bytes, closer and closer to it as more bytes come in.
    """
    if totalBytes > 0:
        ratio = min(bytesRead / totalBytes, 1.0)
    else:
        ratio = bytesRead / (bytesRead + _INSTALL_SIZE_SCALE)
    return start + (end - start) * ratio


def listFiles(folder: Path, skipFolder: Optional[Callable[[str], bool]] = None) -> List[str]:
    """
    Return the files (and links) in "folder" and its subfolders, as sorted paths relative to "folder"
    with POSIX separators.

    Args:
        folder: the folder to list the files of.
        skipFolder: called with the relative path of each subfolder, which is not listed if it returns True.
    """
    files = []
    for root, dirNames, fileNames in os.walk(folder):
        relativeRoot = Path(root).relative_to(folder)
        if skipFolder:
            dirNames[:] = [name for name in dirNames if not skipFolder((relativeRoot / name).as_posix())]
        # A link to a folder is listed as a file, and not walked.
        links = [name for name in dirNames if (Path(root) / name).is_symlink()]
        dirNames[:] = [name for name in dirNames if name not in links]
        files += [(relativeRoot / name).as_posix() for name in fileNames + links]
    return sorted(files)


class PluginInstaller(PluginService):
    """
    Installs a plugin from its PluginProvider into "<pluginsPath>/<pluginName>":
        1. Download the plugin archive.
        2. Extract it, and generate its "plugin.lock".
        3. Install its Python dependencies with "uv" into "<pluginFolder>/venv".
        4. Download the assets declared in its metadata into the plugin folder, or move them from
           "reusableAssets" when they are unchanged.
        5. Record the source, the files and the installed assets of the plugin in its "plugin.lock".

    A plugin is only installed once all of this is done: if the installation fails or is cancelled
    after the plugin folder has been created, the reused assets are moved back and that folder is removed.
    """

    def __init__(self, provider: PluginProvider, record: PluginRecord,
                 version: Optional[str] = None, pluginsPath: Path = meshroomPluginsFolder,
                 reusableAssets: Optional[List[Tuple[PluginInstalledAsset, Path]]] = None) -> None:
        """
        Args:
            provider: the PluginProvider to download the plugin from.
            record: the record describing the plugin to install.
            version: the version to install, or the version of "record" if None.
            pluginsPath: the folder to install the plugin in.
            reusableAssets: assets already installed (e.g. by the previous version of the plugin), with
                            their current location. An asset of the plugin with the same path, the same
                            sha256 and extracted the same way is moved from there instead of downloaded.
        """
        super().__init__("installation", record.name, Path(pluginsPath))
        self._provider: PluginProvider = provider
        self._record: PluginRecord = record
        self._version: str = version or record.version
        self._reusableAssets: Dict[str, Tuple[PluginInstalledAsset, Path]] = {
            installedAsset.path: (installedAsset, location) for installedAsset, location in (reusableAssets or [])}
        # The reused assets, as (location in the plugin, previous location).
        self._reusedAssets: List[Tuple[Path, Path]] = []
        self._installedAssets: List[PluginInstalledAsset] = []
        self._pluginFolder: Optional[Path] = None
        self._metadata: Optional[PluginMetadata] = None

    @property
    def pluginFolder(self) -> Optional[Path]:
        """ The folder the plugin has been installed in, once installed. """
        return self._pluginFolder

    @property
    def metadata(self) -> Optional[PluginMetadata]:
        """ The metadata of the installed plugin, once installed. """
        return self._metadata

    def _run(self) -> None:
        """
        Install the plugin: download it, extract it, install its dependencies, then download its assets.
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
        pluginFolder, metadata = self._extract(content)

        try:
            # Install the plugin's dependencies.
            self._reportProgress("Installing dependencies", _INSTALL_PROGRESS_EXTRACT)
            self._installDependencies(pluginFolder)

            # Download the plugin's assets.
            self._reportProgress("Downloading assets", _INSTALL_PROGRESS_DEPENDENCIES)
            self._downloadAssets(pluginFolder, metadata.assets)

            # Record the installed assets.
            metadata.installedAssets = list(self._installedAssets)
            metadata.writeLockfile(pluginFolder / "plugin.lock")
        except BaseException:
            # Do not leave a half-installed plugin behind, nor lose the assets it reused.
            self.restoreReusedAssets()
            shutil.rmtree(pluginFolder, ignore_errors=True)
            raise

        self._pluginFolder = pluginFolder
        self._metadata = metadata
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

    def _extract(self, content: bytes) -> Tuple[Path, PluginMetadata]:
        """
        Extract the downloaded archive and move the plugin to "<pluginsPath>/<pluginName>", together
        with the "plugin.lock" generated from its metadata.

        Args:
            content: the content of the plugin archive.

        Returns:
            tuple[Path, PluginMetadata]: the plugin folder and the plugin's metadata.
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

            # Generate the "plugin.lock", with the source and the files of the plugin,
            # and move the plugin into the plugins folder.
            metadata.sourceUrl = self._record.url
            metadata.sourceVersion = self._version
            metadata.files = listFiles(extractedRoot)
            metadata.installedAssets = []
            metadata.writeLockfile(extractedRoot / "plugin.lock")
            try:
                os.rename(extractedRoot, pluginFolder)
            except OSError as exc:
                raise self._error("Extraction", f"Failed to move the plugin to '{pluginFolder}'.", exc)

        logging.info(f"Plugin '{self._record.name}' extracted in '{pluginFolder}'")
        return pluginFolder, metadata

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

    def _downloadAssets(self, pluginFolder: Path, assets: List[PluginAsset]) -> None:
        """
        Download the plugin's assets into "pluginFolder", checking their SHA-256 when it is declared or published.
        An asset from a GitHub release uses the file of the release for the current platform, extracted in
        the asset's path if it is an archive. An unchanged reusable asset is moved instead of downloaded.

        Args:
            pluginFolder: the folder of the plugin.
            assets: the assets to download.
        """
        resolvedPluginFolder = pluginFolder.resolve()
        # Spread the assets evenly over the assets part of the overall progress.
        step = (1.0 - _INSTALL_PROGRESS_DEPENDENCIES) / max(len(assets), 1)

        for index, asset in enumerate(assets):
            # Check if the user canceled the service.
            self._checkCancel()

            destination = asset.resolvePath(pluginFolder)
            # Guard against a path escaping the plugin folder (e.g. through a symbolic link).
            if not destination.resolve().is_relative_to(resolvedPluginFolder):
                raise self._error("Assets", f"Asset '{asset.name}' path '{asset.path}' is outside of the plugin folder.")
            if destination.exists():
                raise self._error("Assets", f"Asset '{asset.name}' path '{asset.path}' already exists in the plugin.")

            start = _INSTALL_PROGRESS_DEPENDENCIES + index * step
            message = f"Downloading asset '{asset.name}' ({index + 1}/{len(assets)})"

            def onBytes(bytesRead: int, totalBytes: int) -> None:
                # Raising from here aborts the download.
                self._checkCancel()
                self._reportProgress(message, downloadProgress(bytesRead, totalBytes, start, start + step))

            self._reportProgress(message, start)
            url, fileName, sha256 = self._assetSource(asset)
            extract = asset.release is not None and isArchive(fileName)
            try:
                destination.parent.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                raise self._error("Assets", f"Failed to create the folder of asset '{asset.name}'.", exc)
            if self._reuseAsset(asset, destination, sha256, extract):
                self._installedAssets.append(PluginInstalledAsset(asset.name, asset.path, url, sha256, extract))
                continue
            if extract:
                # Download the archive next to its destination, then extract it in place.
                with scratchFolder(destination.parent, prefix=f".{destination.name}.") as tmpDir:
                    archivePath = tmpDir / fileName
                    digest = self._downloadAsset(asset, url, archivePath, sha256, onBytes)
                    self._checkCancel()
                    self._reportProgress(f"Extracting asset '{asset.name}' ({index + 1}/{len(assets)})", start + step)
                    try:
                        extractArchive(archivePath, destination)
                    except (ValueError, zipfile.BadZipFile, tarfile.TarError, OSError) as exc:
                        raise self._error("Assets", f"Failed to extract asset '{asset.name}' from '{fileName}'.", exc)
            else:
                digest = self._downloadAsset(asset, url, destination, sha256, onBytes)
                if asset.executable:
                    makeExecutable(destination)
            self._installedAssets.append(PluginInstalledAsset(asset.name, asset.path, url, digest, extract))

        # The last asset gives no other occasion to check it (e.g. canceled during its extraction).
        self._checkCancel()

    def _reuseAsset(self, asset: PluginAsset, destination: Path, sha256: Optional[str], extract: bool) -> bool:
        """
        Move the reusable copy of "asset" to "destination", if it is the same file: same path, same sha256
        (which must be known) and extracted the same way.

        Args:
            asset: the asset to install.
            destination: the path of the asset in the plugin folder.
            sha256: the expected SHA-256 hexdigest of the file of the asset, or None if unknown.
            extract: whether the file of the asset is an archive to extract in "destination".

        Returns:
            bool: whether the asset has been reused.
        """
        reusable = self._reusableAssets.get(asset.path)
        if reusable is None or sha256 is None:
            return False
        installedAsset, location = reusable
        if installedAsset.sha256 != sha256 or installedAsset.extracted != extract or not os.path.lexists(location):
            return False
        try:
            os.rename(location, destination)
        except OSError as exc:
            logging.warning(f"Failed to reuse asset '{asset.name}' from '{location}', downloading it instead: {exc}")
            return False
        self._reusedAssets.append((destination, location))
        if asset.executable and not extract:
            makeExecutable(destination)
        logging.info(f"Asset '{asset.name}' of plugin '{self._record.name}' is unchanged, reused from '{location}'.")
        return True

    def restoreReusedAssets(self) -> None:
        """ Move the reused assets back to their previous location. """
        for destination, location in reversed(self._reusedAssets):
            try:
                os.rename(destination, location)
            except OSError as exc:
                logging.error(f"Failed to move asset '{destination}' back to '{location}': {exc}")
        self._reusedAssets.clear()

    def _assetSource(self, asset: PluginAsset) -> Tuple[str, str, Optional[str]]:
        """
        Return where to download "asset" from: its url, or the file of its GitHub release for the current platform.

        Args:
            asset: the asset to download.

        Returns:
            tuple[str, str, str | None]: the url of the file to download, its file name, and its expected
            SHA-256 hexdigest (None if unknown).
        """
        if asset.release is None:
            return asset.url, PurePosixPath(asset.path).name, asset.sha256
        try:
            releaseFile = selectReleaseFile(fetchReleaseFiles(asset.release), *currentPlatform())
        except ReleaseError as exc:
            raise self._error("Assets", f"Cannot download asset '{asset.name}' from release '{asset.release}'.", exc)
        logging.info(f"Asset '{asset.name}' of plugin '{self._record.name}': "
                     f"using '{releaseFile.name}' of release '{asset.release}'.")
        return releaseFile.url, releaseFile.name, releaseFile.sha256

    def _downloadAsset(self, asset: PluginAsset, url: str, destination: Path, sha256: Optional[str],
                       onBytes: Callable[[int, int], None]) -> str:
        """
        Download the file "url" of "asset" into "destination", and check it against "sha256".

        Args:
            asset: the asset being downloaded.
            url: the url of the file to download.
            destination: the file to write. Its parent folder must exist.
            sha256: the expected SHA-256 hexdigest of the file, or None if unknown.
            onBytes: the progress callback of the download, see fetchToFile().

        Returns:
            str: the SHA-256 hexdigest of the downloaded file.
        """
        logging.info(f"Downloading asset '{asset.name}' of plugin '{self._record.name}' from '{url}'...")
        try:
            digest = fetchToFile(url, destination, onBytes=onBytes)
        except (RequestError, OSError) as exc:
            raise self._error("Assets", f"Failed to download asset '{asset.name}' from '{url}'.", exc)

        if sha256 is None:
            logging.warning(f"Asset '{asset.name}' of plugin '{self._record.name}' has no declared or published "
                            f"'sha256', its integrity was not checked (downloaded sha256: {digest}).")
        elif digest != sha256:
            destination.unlink()
            raise self._error("Assets", f"Checksum mismatch for asset '{asset.name}': "
                                        f"expected sha256 {sha256}, got {digest}.")
        return digest

    def _runUv(self, uv: str, args: List[str], env: Optional[dict] = None) -> None:
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
        output: List[str] = []

        def onLine(line: str) -> None:
            nonlocal progress
            self._checkCancel()
            # "progress" is the progress of this command
            #  Map it to the dependencies part of the overall progress.
            progress = parseUvProgress(line, progress)
            dependenciesRange = _INSTALL_PROGRESS_DEPENDENCIES - _INSTALL_PROGRESS_EXTRACT
            self._reportProgress("Installing dependencies", _INSTALL_PROGRESS_EXTRACT + dependenciesRange * progress)

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
