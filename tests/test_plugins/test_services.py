#!/usr/bin/env python
# coding:utf-8

import hashlib
import json
import os
import stat
import tarfile

from pathlib import Path

import pytest

from meshroom.core.plugins.metadata import PluginInstalledAsset
from meshroom.core.plugins.record import PluginRecord
from meshroom.core.plugins.local import installer as installerModule, releases
from meshroom.core.plugins.provider import ArchivePluginProvider
from meshroom.core.plugins.local.service import PluginServiceCancelled, PluginServiceError
from meshroom.core.plugins.local.installer import PluginInstaller
from meshroom.core.plugins.local.uninstaller import PluginUninstaller
from meshroom.core.plugins.local.updater import PluginUpdater
from ..utils import writeFile, writeZip


def writePluginZip(zipPath, version="1.0", name="myPlugin", assets=None, files=None):
    """
    Write a plugin archive whose "meshroom/config.json" declares "name", "version" and "assets".
    "files" are extra files to add to the archive, as {pathInPlugin: content}.
    """
    # Use the legacy "config.json" rather than a "pyproject.toml", which would trigger a "uv sync"
    # of the plugin's dependencies on installation.
    config = {"name": name, "version": version, "assets": assets or []}
    content = {"root/meshroom/config.json": json.dumps(config)}
    content.update({f"root/{path}": fileContent for path, fileContent in (files or {}).items()})
    return writeZip(zipPath, content)


def asset(url, name="weights", path="weights.pt", sha256=None):
    """ Return an asset entry of a plugin metadata file. """
    entry = {"name": name, "category": "model", "url": url, "path": path}
    if sha256 is not None:
        entry["sha256"] = sha256
    return entry


def releaseAsset(release="myOrg/myTool@v1.0", name="tool", path="tool", executable=False):
    """ Return an asset entry of a plugin metadata file, coming from a GitHub release. """
    entry = {"name": name, "category": "binary", "release": release, "path": path}
    if executable:
        entry["executable"] = True
    return entry


def sha256Of(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def isExecutable(path):
    return bool(path.stat().st_mode & stat.S_IXUSR)


def installer(archive, pluginsPath, name="myPlugin", reusableAssets=None):
    """ Return a PluginInstaller for the plugin archive "archive". """
    record = PluginRecord(name, "1.0", "me", archive.as_uri())
    return PluginInstaller(ArchivePluginProvider(archive.as_uri()), record, pluginsPath=pluginsPath,
                           reusableAssets=reusableAssets)


def updater(archive, pluginsPath, name="myPlugin", installedName=None):
    """ Return a PluginUpdater for the plugin archive "archive". """
    record = PluginRecord(name, "2.0", "me", archive.as_uri())
    return PluginUpdater(ArchivePluginProvider(archive.as_uri()), record, pluginsPath=pluginsPath,
                         installedName=installedName)


def readLock(pluginFolder):
    """ Return the content of the "plugin.lock" of the plugin installed in "pluginFolder". """
    return json.loads((pluginFolder / "plugin.lock").read_text())


def lockVersion(pluginFolder):
    """ Return the version written in the "plugin.lock" of the plugin installed in "pluginFolder". """
    return readLock(pluginFolder)["version"]


class TestInstaller:

    def test_install(self, tmp_path):
        """ The plugin is extracted in the plugins folder, with a "plugin.lock" built from its metadata. """
        archive = writePluginZip(tmp_path / "plugin.zip")
        installer(archive, tmp_path / "plugins").execute()

        pluginFolder = tmp_path / "plugins" / "myPlugin"
        assert (pluginFolder / "meshroom" / "config.json").is_file()
        assert lockVersion(pluginFolder) == "1.0"
        assert json.loads((pluginFolder / "plugin.lock").read_text())["publisher"] == "me"

    def test_nameFromMetadata(self, tmp_path):
        """ The plugin folder is named after the plugin's metadata, not after its record. """
        archive = writePluginZip(tmp_path / "plugin.zip", name="metadataName")
        installer(archive, tmp_path / "plugins", name="recordName").execute()
        assert (tmp_path / "plugins" / "metadataName").is_dir()
        assert not (tmp_path / "plugins" / "recordName").exists()

    def test_nameFromRecord(self, tmp_path):
        """ Without metadata, the plugin is named and versioned after its record. """
        archive = writeZip(tmp_path / "plugin.zip", {"root/meshroom/__init__.py": ""})
        installer(archive, tmp_path / "plugins").execute()
        assert lockVersion(tmp_path / "plugins" / "myPlugin") == "1.0"

    def test_alreadyInstalled(self, tmp_path):
        """ An installed plugin cannot be installed again. """
        writeFile(tmp_path / "plugins" / "myPlugin" / "file.txt")
        archive = writePluginZip(tmp_path / "plugin.zip")
        with pytest.raises(PluginServiceError):
            installer(archive, tmp_path / "plugins").execute()

    def test_missingArchive(self, tmp_path):
        """ An archive that cannot be downloaded fails the installation. """
        with pytest.raises(PluginServiceError):
            installer(tmp_path / "missing.zip", tmp_path / "plugins").execute()
        assert not (tmp_path / "plugins" / "myPlugin").exists()

    def test_invalidArchives(self, tmp_path):
        """ An invalid archive fails the installation, and leaves nothing behind in the plugins folder. """
        archives = [
            writeFile(tmp_path / "notAZip.zip", "not a zip"),
            writeZip(tmp_path / "unsafe.zip", {"root/../evil.txt": ""}),
            writeZip(tmp_path / "twoRoots.zip", {"rootA/file.txt": "", "rootB/file.txt": ""}),
        ]
        for archive in archives:
            with pytest.raises(PluginServiceError):
                installer(archive, tmp_path / "plugins").execute()
            assert list((tmp_path / "plugins").iterdir()) == []
        assert not (tmp_path / "evil.txt").exists()

    def test_cancel(self, tmp_path):
        """ A cancelled installation leaves nothing behind. """
        archive = writePluginZip(tmp_path / "plugin.zip")
        with pytest.raises(PluginServiceCancelled):
            installer(archive, tmp_path / "plugins").execute(isCancelled=lambda: True)
        assert not (tmp_path / "plugins" / "myPlugin").exists()

    def test_assets(self, tmp_path):
        """ The declared assets are downloaded into the plugin folder, checked against their sha256. """
        assetFile = writeFile(tmp_path / "remote" / "weights.pt", "weights")
        sha256 = hashlib.sha256(b"weights").hexdigest()
        archive = writePluginZip(tmp_path / "plugin.zip", assets=[
            asset(assetFile.as_uri(), path="models/sub/weights.pt", sha256=sha256),
            asset(assetFile.as_uri(), name="rootWeights"),
        ])
        installer(archive, tmp_path / "plugins").execute()

        pluginFolder = tmp_path / "plugins" / "myPlugin"
        assert (pluginFolder / "models" / "sub" / "weights.pt").read_text() == "weights"
        assert (pluginFolder / "weights.pt").read_text() == "weights"
        lockAssets = json.loads((pluginFolder / "plugin.lock").read_text())["assets"]
        assert [entry["path"] for entry in lockAssets] == ["models/sub/weights.pt", "weights.pt"]

    def test_lockRecordsInstallation(self, tmp_path):
        """ The "plugin.lock" records the source, the files of the archive and the installed assets. """
        assetFile = writeFile(tmp_path / "remote" / "weights.pt", "weights")
        archive = writePluginZip(tmp_path / "plugin.zip", assets=[asset(assetFile.as_uri())],
                                 files={"meshroom/node.py": ""})
        installer(archive, tmp_path / "plugins").execute()

        lock = readLock(tmp_path / "plugins" / "myPlugin")
        assert lock["source"] == {"url": archive.as_uri(), "version": "1.0"}
        assert lock["files"] == ["meshroom/config.json", "meshroom/node.py"]
        assert lock["installedAssets"] == [{"name": "weights", "path": "weights.pt", "url": assetFile.as_uri(),
                                            "sha256": sha256Of(assetFile), "extracted": False}]

    def test_reuseAssets(self, tmp_path):
        """ A reusable asset with the same path and sha256 is moved instead of downloaded, another one is not. """
        sha256 = hashlib.sha256(b"weights").hexdigest()
        reusable = writeFile(tmp_path / "previous" / "weights.pt", "weights")
        changed = writeFile(tmp_path / "previous" / "other.pt", "old")
        newFile = writeFile(tmp_path / "remote" / "other.pt", "new")
        archive = writePluginZip(tmp_path / "plugin.zip", assets=[
            # The url does not exist: the asset can only be installed from the reusable one.
            asset((tmp_path / "missing.pt").as_uri(), sha256=sha256),
            asset(newFile.as_uri(), name="other", path="other.pt", sha256=sha256Of(newFile)),
        ])
        installer(archive, tmp_path / "plugins", reusableAssets=[
            (PluginInstalledAsset("weights", "weights.pt", "https://old", sha256), reusable),
            (PluginInstalledAsset("other", "other.pt", "https://old", hashlib.sha256(b"old").hexdigest()), changed),
        ]).execute()

        pluginFolder = tmp_path / "plugins" / "myPlugin"
        assert (pluginFolder / "weights.pt").read_text() == "weights"
        assert not reusable.exists()
        assert (pluginFolder / "other.pt").read_text() == "new"
        assert changed.read_text() == "old"
        assert [entry["sha256"] for entry in readLock(pluginFolder)["installedAssets"]] == [sha256, sha256Of(newFile)]

    def test_failureRestoresReusedAssets(self, tmp_path):
        """ When the installation fails, the reused assets are moved back. """
        sha256 = hashlib.sha256(b"weights").hexdigest()
        reusable = writeFile(tmp_path / "previous" / "weights.pt", "weights")
        archive = writePluginZip(tmp_path / "plugin.zip", assets=[
            asset((tmp_path / "missing.pt").as_uri(), sha256=sha256),
            asset((tmp_path / "missing.pt").as_uri(), name="other", path="other.pt"),
        ])
        with pytest.raises(PluginServiceError):
            installer(archive, tmp_path / "plugins", reusableAssets=[
                (PluginInstalledAsset("weights", "weights.pt", "https://old", sha256), reusable)]).execute()
        assert reusable.read_text() == "weights"
        assert not (tmp_path / "plugins" / "myPlugin").exists()

    def test_assetChecksumMismatch(self, tmp_path):
        """ An asset that does not match its sha256 fails the installation, and leaves nothing behind. """
        assetFile = writeFile(tmp_path / "remote" / "weights.pt", "weights")
        archive = writePluginZip(tmp_path / "plugin.zip", assets=[asset(assetFile.as_uri(), sha256="0" * 64)])
        with pytest.raises(PluginServiceError):
            installer(archive, tmp_path / "plugins").execute()
        assert not (tmp_path / "plugins" / "myPlugin").exists()

    def test_missingAsset(self, tmp_path):
        """ An asset that cannot be downloaded fails the installation, and leaves nothing behind. """
        archive = writePluginZip(tmp_path / "plugin.zip", assets=[asset((tmp_path / "missing.pt").as_uri())])
        with pytest.raises(PluginServiceError):
            installer(archive, tmp_path / "plugins").execute()
        assert not (tmp_path / "plugins" / "myPlugin").exists()

    def test_assetConflictsWithPluginFile(self, tmp_path):
        """ An asset cannot overwrite a file shipped with the plugin. """
        assetFile = writeFile(tmp_path / "remote" / "weights.pt", "weights")
        archive = writePluginZip(tmp_path / "plugin.zip", assets=[asset(assetFile.as_uri())],
                                 files={"weights.pt": "shipped"})
        with pytest.raises(PluginServiceError):
            installer(archive, tmp_path / "plugins").execute()
        assert not (tmp_path / "plugins" / "myPlugin").exists()


class TestReleaseAssets:
    """ Assets coming from GitHub releases, with the GitHub API served from local files. """

    @pytest.fixture(autouse=True)
    def api(self, tmp_path, monkeypatch):
        monkeypatch.setattr(releases, "_GITHUB_API_URL", (tmp_path / "api").as_uri())
        self.setPlatform(monkeypatch, "linux", "x86_64")
        return tmp_path / "api"

    @staticmethod
    def setPlatform(monkeypatch, system, arch):
        monkeypatch.setattr(installerModule, "currentPlatform", lambda: (system, arch))

    @staticmethod
    def publishRelease(api, files, release="myOrg/myTool@v1.0", digests=None):
        """ Publish the release "release" with the local "files", whose digests are their sha256 unless given. """
        repository, _, tag = release.partition("@")
        digests = digests or {}
        assets = [{"name": file.name, "browser_download_url": file.as_uri(),
                   "digest": digests.get(file.name, "sha256:" + sha256Of(file))} for file in files]
        writeFile(api / "repos" / repository / "releases" / "tags" / tag, json.dumps({"assets": assets}))

    @staticmethod
    def writeToolArchives(folder):
        """ Write a Linux tar.gz and a Windows zip archive of a tool, each with a single root folder. """
        linuxArchive = folder / "tool-1.0-linux-x86_64.tar.gz"
        executable = writeFile(folder / "build" / "tool-1.0" / "bin" / "tool", "linux")
        executable.chmod(0o755)
        writeFile(folder / "build" / "tool-1.0" / "data.txt", "data")
        with tarfile.open(linuxArchive, "w:gz") as archive:
            archive.add(folder / "build" / "tool-1.0", arcname="tool-1.0")
        windowsArchive = writeZip(folder / "tool-1.0-windows-x86_64.zip", {"tool-1.0/bin/tool.exe": "windows"})
        return linuxArchive, windowsArchive

    def test_archive(self, tmp_path, api):
        """ The archive of the release for the current platform is extracted in the asset's path. """
        self.publishRelease(api, self.writeToolArchives(tmp_path / "remote"))
        archive = writePluginZip(tmp_path / "plugin.zip", assets=[releaseAsset(path="bin/tool")])
        installer(archive, tmp_path / "plugins").execute()

        toolFolder = tmp_path / "plugins" / "myPlugin" / "bin" / "tool"
        assert (toolFolder / "bin" / "tool").read_text() == "linux"
        assert (toolFolder / "data.txt").read_text() == "data"
        if os.name != "nt":
            assert isExecutable(toolFolder / "bin" / "tool")
        # Nothing is left from the download.
        assert sorted(path.name for path in toolFolder.parent.iterdir()) == ["tool"]

    def test_platform(self, tmp_path, api, monkeypatch):
        self.publishRelease(api, self.writeToolArchives(tmp_path / "remote"))
        self.setPlatform(monkeypatch, "windows", "x86_64")
        archive = writePluginZip(tmp_path / "plugin.zip", assets=[releaseAsset()])
        installer(archive, tmp_path / "plugins").execute()
        assert (tmp_path / "plugins" / "myPlugin" / "tool" / "bin" / "tool.exe").read_text() == "windows"

    def test_noFileForPlatform(self, tmp_path, api, monkeypatch):
        """ A release without a file for the current platform fails the installation, and leaves nothing behind. """
        self.publishRelease(api, self.writeToolArchives(tmp_path / "remote"))
        self.setPlatform(monkeypatch, "macos", "arm64")
        archive = writePluginZip(tmp_path / "plugin.zip", assets=[releaseAsset()])
        with pytest.raises(PluginServiceError, match="tool-1.0-linux-x86_64.tar.gz"):
            installer(archive, tmp_path / "plugins").execute()
        assert not (tmp_path / "plugins" / "myPlugin").exists()

    def test_cancelDuringExtraction(self, tmp_path, api, monkeypatch):
        """ A cancellation during the extraction of the last asset cancels the installation. """
        self.publishRelease(api, self.writeToolArchives(tmp_path / "remote"))
        archive = writePluginZip(tmp_path / "plugin.zip", assets=[releaseAsset()])
        extractArchive = installerModule.extractArchive
        extracted = []

        def extractThenCancel(archivePath, destination):
            extractArchive(archivePath, destination)
            extracted.append(destination)

        monkeypatch.setattr(installerModule, "extractArchive", extractThenCancel)
        with pytest.raises(PluginServiceCancelled):
            installer(archive, tmp_path / "plugins").execute(isCancelled=lambda: bool(extracted))
        assert extracted
        assert not (tmp_path / "plugins" / "myPlugin").exists()

    def test_assetFolderIsAFile(self, tmp_path, api):
        """ A folder of the asset's path that cannot be created fails the installation like any other error. """
        self.publishRelease(api, self.writeToolArchives(tmp_path / "remote"))
        archive = writePluginZip(tmp_path / "plugin.zip", assets=[releaseAsset(path="bin/tool")], files={"bin": "file"})
        with pytest.raises(PluginServiceError, match="Failed to create the folder"):
            installer(archive, tmp_path / "plugins").execute()
        assert not (tmp_path / "plugins" / "myPlugin").exists()

    def test_missingRelease(self, tmp_path):
        archive = writePluginZip(tmp_path / "plugin.zip", assets=[releaseAsset()])
        with pytest.raises(PluginServiceError):
            installer(archive, tmp_path / "plugins").execute()
        assert not (tmp_path / "plugins" / "myPlugin").exists()

    def test_digestMismatch(self, tmp_path, api):
        """ A file that does not match the digest published by GitHub fails the installation. """
        linuxArchive, windowsArchive = self.writeToolArchives(tmp_path / "remote")
        self.publishRelease(api, [linuxArchive, windowsArchive], digests={linuxArchive.name: "sha256:" + "0" * 64})
        archive = writePluginZip(tmp_path / "plugin.zip", assets=[releaseAsset()])
        with pytest.raises(PluginServiceError, match="Checksum mismatch"):
            installer(archive, tmp_path / "plugins").execute()
        assert not (tmp_path / "plugins" / "myPlugin").exists()

    def test_invalidArchive(self, tmp_path, api):
        broken = writeFile(tmp_path / "remote" / "tool-linux-x86_64.tar.gz", "notAnArchive")
        self.publishRelease(api, [broken])
        archive = writePluginZip(tmp_path / "plugin.zip", assets=[releaseAsset()])
        with pytest.raises(PluginServiceError, match="Failed to extract"):
            installer(archive, tmp_path / "plugins").execute()
        assert not (tmp_path / "plugins" / "myPlugin").exists()

    def test_updateKeepsUnchangedArchive(self, tmp_path, api):
        """ An update keeps the extracted archive of an unchanged release, and downloads a changed one. """
        linuxArchive, windowsArchive = self.writeToolArchives(tmp_path / "remote")
        self.publishRelease(api, [linuxArchive, windowsArchive])
        assets = [releaseAsset()]
        installer(writePluginZip(tmp_path / "v1.zip", "1.0", assets=assets), tmp_path / "plugins").execute()
        toolFolder = tmp_path / "plugins" / "myPlugin" / "tool"
        writeFile(toolFolder / "generated.txt", "generated")

        # The release is unchanged but cannot be downloaded anymore: the update must keep the installed one.
        linuxArchive.unlink()
        updater(writePluginZip(tmp_path / "v2.zip", "2.0", assets=assets), tmp_path / "plugins").execute()
        assert (toolFolder / "generated.txt").read_text() == "generated"
        assert readLock(tmp_path / "plugins" / "myPlugin")["installedAssets"][0]["extracted"] is True

        # A new release is downloaded.
        newArchive = writeZip(tmp_path / "remote" / "tool-2.0-linux-x86_64.zip", {"tool-2.0/bin/tool": "linux 2.0"})
        self.publishRelease(api, [newArchive], release="myOrg/myTool@v2.0")
        updater(writePluginZip(tmp_path / "v3.zip", "3.0", assets=[releaseAsset("myOrg/myTool@v2.0")]),
                tmp_path / "plugins").execute()
        assert (toolFolder / "bin" / "tool").read_text() == "linux 2.0"
        assert not (toolFolder / "generated.txt").exists()

    def test_executableFile(self, tmp_path, api):
        """ A release file that is not an archive is downloaded as is in the asset's path, and made executable. """
        linuxTool = writeFile(tmp_path / "remote" / "tool-linux-x86_64", "linux")
        windowsTool = writeFile(tmp_path / "remote" / "tool-windows-x86_64.exe", "windows")
        self.publishRelease(api, [linuxTool, windowsTool])
        archive = writePluginZip(tmp_path / "plugin.zip", assets=[releaseAsset(path="bin/tool", executable=True)])
        installer(archive, tmp_path / "plugins").execute()

        tool = tmp_path / "plugins" / "myPlugin" / "bin" / "tool"
        assert tool.read_text() == "linux"
        if os.name != "nt":
            assert isExecutable(tool)

    @pytest.mark.skipif(os.name == "nt", reason="No executable permission on Windows.")
    def test_executableUrlAsset(self, tmp_path):
        assetFile = writeFile(tmp_path / "remote" / "tool", "tool")
        entry = dict(asset(assetFile.as_uri(), path="tool"), executable=True)
        archive = writePluginZip(tmp_path / "plugin.zip", assets=[entry])
        installer(archive, tmp_path / "plugins").execute()
        assert isExecutable(tmp_path / "plugins" / "myPlugin" / "tool")


class TestUninstaller:

    def test_uninstall(self, tmp_path):
        """ The plugin folder is removed. """
        writeFile(tmp_path / "plugins" / "myPlugin" / "file.txt")
        PluginUninstaller("myPlugin", tmp_path / "plugins").execute()
        assert list((tmp_path / "plugins").iterdir()) == []

    def test_notInstalled(self, tmp_path):
        """ A plugin that is not installed cannot be uninstalled. """
        with pytest.raises(PluginServiceError):
            PluginUninstaller("myPlugin", tmp_path / "plugins").execute()

    @pytest.mark.parametrize("name", ["..", ".", "", "a/b"])
    def test_invalidName(self, tmp_path, name):
        """ A name that is not a plain folder name is rejected, and nothing is removed. """
        writeFile(tmp_path / "plugins" / "file.txt")
        with pytest.raises(PluginServiceError):
            PluginUninstaller(name, tmp_path / "plugins").execute()
        assert (tmp_path / "plugins" / "file.txt").is_file()


class TestUpdater:

    def test_update(self, tmp_path):
        """ The installed plugin is replaced by the new version, and its backup is removed. """
        installer(writePluginZip(tmp_path / "v1.zip", "1.0"), tmp_path / "plugins").execute()
        updater(writePluginZip(tmp_path / "v2.zip", "2.0"), tmp_path / "plugins").execute()
        assert lockVersion(tmp_path / "plugins" / "myPlugin") == "2.0"
        assert [p.name for p in (tmp_path / "plugins").iterdir()] == ["myPlugin"]

    def test_notInstalled(self, tmp_path):
        """ A plugin that is not installed cannot be updated. """
        with pytest.raises(PluginServiceError):
            updater(writePluginZip(tmp_path / "v2.zip", "2.0"), tmp_path / "plugins").execute()

    def test_failedUpdateRestoresPlugin(self, tmp_path):
        """ When the new version cannot be installed, the installed plugin is put back. """
        installer(writePluginZip(tmp_path / "v1.zip", "1.0"), tmp_path / "plugins").execute()
        with pytest.raises(PluginServiceError):
            updater(writeFile(tmp_path / "v2.zip", "not a zip"), tmp_path / "plugins").execute()
        assert lockVersion(tmp_path / "plugins" / "myPlugin") == "1.0"
        assert [p.name for p in (tmp_path / "plugins").iterdir()] == ["myPlugin"]

    def test_keepsUnchangedAssets(self, tmp_path):
        """ An asset with the same path and sha256 is kept, a changed one is downloaded again. """
        weights = writeFile(tmp_path / "remote" / "weights.pt", "weights")
        other = writeFile(tmp_path / "remote" / "other.pt", "old")
        installer(writePluginZip(tmp_path / "v1.zip", "1.0", assets=[
            asset(weights.as_uri(), sha256=sha256Of(weights)),
            asset(other.as_uri(), name="other", path="other.pt", sha256=sha256Of(other)),
        ]), tmp_path / "plugins").execute()

        # The unchanged asset cannot be downloaded anymore: the update must keep the installed one.
        weights.unlink()
        newOther = writeFile(tmp_path / "remote" / "newOther.pt", "new")
        updater(writePluginZip(tmp_path / "v2.zip", "2.0", assets=[
            asset(weights.as_uri(), sha256=hashlib.sha256(b"weights").hexdigest()),
            asset(newOther.as_uri(), name="other", path="other.pt", sha256=sha256Of(newOther)),
        ]), tmp_path / "plugins").execute()

        pluginFolder = tmp_path / "plugins" / "myPlugin"
        assert (pluginFolder / "weights.pt").read_text() == "weights"
        assert (pluginFolder / "other.pt").read_text() == "new"
        assert [p.name for p in (tmp_path / "plugins").iterdir()] == ["myPlugin"]

    def test_assetWithoutSha256IsDownloadedAgain(self, tmp_path):
        """ An asset without a known sha256 cannot be compared, it is downloaded again. """
        weights = writeFile(tmp_path / "remote" / "weights.pt", "old")
        installer(writePluginZip(tmp_path / "v1.zip", "1.0", assets=[asset(weights.as_uri())]), tmp_path / "plugins").execute()
        weights.write_text("new")
        updater(writePluginZip(tmp_path / "v2.zip", "2.0", assets=[asset(weights.as_uri())]), tmp_path / "plugins").execute()
        assert (tmp_path / "plugins" / "myPlugin" / "weights.pt").read_text() == "new"

    def test_carriesOverAddedFiles(self, tmp_path):
        """ The files added to the plugin are carried over, not the files of the previous version, nor generated ones. """
        weights = writeFile(tmp_path / "remote" / "weights.pt", "weights")
        installer(writePluginZip(tmp_path / "v1.zip", "1.0", assets=[asset(weights.as_uri())],
                                 files={"meshroom/removed.py": "", "meshroom/kept.py": "v1"}), tmp_path / "plugins").execute()
        pluginFolder = tmp_path / "plugins" / "myPlugin"
        writeFile(pluginFolder / "data" / "user.txt", "user")
        writeFile(pluginFolder / "meshroom" / "local.py", "user")
        writeFile(pluginFolder / "meshroom" / "__pycache__" / "removed.pyc")
        writeFile(pluginFolder / "venv" / "lib" / "package.py")
        writeFile(pluginFolder / "uv.lock")

        updater(writePluginZip(tmp_path / "v2.zip", "2.0", files={"meshroom/kept.py": "v2"}), tmp_path / "plugins").execute()

        assert (pluginFolder / "data" / "user.txt").read_text() == "user"
        assert (pluginFolder / "meshroom" / "local.py").read_text() == "user"
        assert (pluginFolder / "meshroom" / "kept.py").read_text() == "v2"
        assert not (pluginFolder / "meshroom" / "removed.py").exists()
        assert not (pluginFolder / "meshroom" / "__pycache__").exists()
        assert not (pluginFolder / "venv").exists()
        assert not (pluginFolder / "uv.lock").exists()
        # The asset is no longer declared.
        assert not (pluginFolder / "weights.pt").exists()

    def test_addedFileReplacedByNewVersion(self, tmp_path):
        """ An added file whose path is taken by the new version is carried over next to it. """
        installer(writePluginZip(tmp_path / "v1.zip", "1.0"), tmp_path / "plugins").execute()
        pluginFolder = tmp_path / "plugins" / "myPlugin"
        writeFile(pluginFolder / "notes.txt", "user")
        updater(writePluginZip(tmp_path / "v2.zip", "2.0", files={"notes.txt": "v2"}), tmp_path / "plugins").execute()
        assert (pluginFolder / "notes.txt").read_text() == "v2"
        assert (pluginFolder / "notes.txt.previous").read_text() == "user"

    @pytest.mark.parametrize("userFile, files", [
        ("notes.txt", {"notes.txt": "v2", "notes.txt.previous": "v2"}),
        ("data/notes.txt", {"data": "v2"}),
    ])
    def test_addedFileWithoutPath(self, tmp_path, userFile, files):
        """ An added file the new version leaves no path for fails the update, rather than being lost. """
        weights = writeFile(tmp_path / "remote" / "weights.pt", "weights")
        assets = [asset(weights.as_uri(), sha256=sha256Of(weights))]
        installer(writePluginZip(tmp_path / "v1.zip", "1.0", assets=assets), tmp_path / "plugins").execute()
        pluginFolder = tmp_path / "plugins" / "myPlugin"
        writeFile(pluginFolder / userFile, "user")
        with pytest.raises(PluginServiceError, match="carry over"):
            updater(writePluginZip(tmp_path / "v2.zip", "2.0", assets=assets, files=files), tmp_path / "plugins").execute()
        assert lockVersion(pluginFolder) == "1.0"
        assert (pluginFolder / userFile).read_text() == "user"
        assert (pluginFolder / "weights.pt").read_text() == "weights"

    def test_addedFileInNewAssetPath(self, tmp_path):
        """ An added file in the path of an asset of the new version is not carried over. """
        installer(writePluginZip(tmp_path / "v1.zip", "1.0"), tmp_path / "plugins").execute()
        pluginFolder = tmp_path / "plugins" / "myPlugin"
        writeFile(pluginFolder / "models" / "byHand.pt", "user")
        weights = writeFile(tmp_path / "remote" / "weights.pt", "weights")
        updater(writePluginZip(tmp_path / "v2.zip", "2.0", assets=[asset(weights.as_uri(), path="models")]),
                tmp_path / "plugins").execute()
        assert (pluginFolder / "models").read_text() == "weights"

    def test_lockWithoutInstallation(self, tmp_path):
        """
        A plugin installed before its installation was recorded keeps its declared assets with a sha256,
        but its added files cannot be told apart from the files of its archive: none is carried over.
        """
        weights = writeFile(tmp_path / "remote" / "weights.pt", "weights")
        assets = [asset(weights.as_uri(), sha256=sha256Of(weights))]
        installer(writePluginZip(tmp_path / "v1.zip", "1.0", assets=assets), tmp_path / "plugins").execute()
        pluginFolder = tmp_path / "plugins" / "myPlugin"
        lock = readLock(pluginFolder)
        for key in ("source", "installedAssets", "files"):
            del lock[key]
        writeFile(pluginFolder / "plugin.lock", json.dumps(lock))
        writeFile(pluginFolder / "user.txt", "user")

        weights.unlink()
        updater(writePluginZip(tmp_path / "v2.zip", "2.0", assets=assets), tmp_path / "plugins").execute()
        assert (pluginFolder / "weights.pt").read_text() == "weights"
        assert not (pluginFolder / "user.txt").exists()

    def test_failedUpdateKeepsAssetsAndFiles(self, tmp_path):
        """ When the new version cannot be installed, the installed plugin is put back with its assets and files. """
        weights = writeFile(tmp_path / "remote" / "weights.pt", "weights")
        assets = [asset(weights.as_uri(), sha256=sha256Of(weights))]
        installer(writePluginZip(tmp_path / "v1.zip", "1.0", assets=assets), tmp_path / "plugins").execute()
        pluginFolder = tmp_path / "plugins" / "myPlugin"
        writeFile(pluginFolder / "user.txt", "user")

        missing = asset((tmp_path / "missing.pt").as_uri(), name="missing", path="missing.pt")
        with pytest.raises(PluginServiceError):
            updater(writePluginZip(tmp_path / "v2.zip", "2.0", assets=assets + [missing]), tmp_path / "plugins").execute()
        assert lockVersion(pluginFolder) == "1.0"
        assert (pluginFolder / "weights.pt").read_text() == "weights"
        assert (pluginFolder / "user.txt").read_text() == "user"
        assert [p.name for p in (tmp_path / "plugins").iterdir()] == ["myPlugin"]

    def test_failedCarryOverRestoresPlugin(self, tmp_path, monkeypatch):
        """ When the added files cannot be carried over, the installed plugin is put back as it was. """
        weights = writeFile(tmp_path / "remote" / "weights.pt", "weights")
        assets = [asset(weights.as_uri(), sha256=sha256Of(weights))]
        installer(writePluginZip(tmp_path / "v1.zip", "1.0", assets=assets), tmp_path / "plugins").execute()
        pluginFolder = tmp_path / "plugins" / "myPlugin"
        writeFile(pluginFolder / "a.txt", "a")
        writeFile(pluginFolder / "b.txt", "b")

        rename = os.rename

        def failingRename(source, destination):
            if str(source).endswith("b.txt"):
                raise OSError("Cannot move")
            rename(source, destination)

        monkeypatch.setattr(os, "rename", failingRename)
        with pytest.raises(PluginServiceError, match="carry over"):
            updater(writePluginZip(tmp_path / "v2.zip", "2.0", assets=assets), tmp_path / "plugins").execute()
        monkeypatch.undo()

        assert lockVersion(pluginFolder) == "1.0"
        assert sorted(p.name for p in pluginFolder.iterdir()) == ["a.txt", "b.txt", "meshroom", "plugin.lock", "weights.pt"]
        assert [p.name for p in (tmp_path / "plugins").iterdir()] == ["myPlugin"]

    def test_failedMoveBackKeepsFiles(self, tmp_path, monkeypatch):
        """ What cannot be moved back after a failed carry over is not deleted with the new version. """
        weights = writeFile(tmp_path / "remote" / "weights.pt", "weights")
        assets = [asset(weights.as_uri(), sha256=sha256Of(weights))]
        installer(writePluginZip(tmp_path / "v1.zip", "1.0", assets=assets), tmp_path / "plugins").execute()
        pluginFolder = tmp_path / "plugins" / "myPlugin"
        writeFile(pluginFolder / "a.txt", "a")
        writeFile(pluginFolder / "b.txt", "b")

        rename = os.rename

        def failingRename(source, destination):
            # Carrying over "b.txt" fails, and so does moving "a.txt" and the asset back.
            if str(source).endswith("b.txt") or (Path(source).parent == pluginFolder and Path(source).name != "myPlugin"):
                raise OSError("Cannot move")
            rename(source, destination)

        monkeypatch.setattr(os, "rename", failingRename)
        with pytest.raises(PluginServiceError, match="carry over"):
            updater(writePluginZip(tmp_path / "v2.zip", "2.0", assets=assets), tmp_path / "plugins").execute()
        monkeypatch.undo()

        assert (pluginFolder / "a.txt").read_text() == "a"
        assert (pluginFolder / "weights.pt").read_text() == "weights"
        # The previous version is still there, for the user to get it back.
        backup = next(path for path in (tmp_path / "plugins").iterdir() if path.name != "myPlugin")
        assert (backup / "b.txt").read_text() == "b"

    def test_failedInstallationKeepsReusedAssets(self, tmp_path, monkeypatch):
        """ A reused asset that cannot be moved back after a failed installation is not deleted with it. """
        weights = writeFile(tmp_path / "remote" / "weights.pt", "weights")
        assets = [asset(weights.as_uri(), sha256=sha256Of(weights))]
        installer(writePluginZip(tmp_path / "v1.zip", "1.0", assets=assets), tmp_path / "plugins").execute()
        pluginFolder = tmp_path / "plugins" / "myPlugin"

        rename = os.rename

        def failingRename(source, destination):
            if Path(source) == pluginFolder / "weights.pt":
                raise OSError("Cannot move")
            rename(source, destination)

        monkeypatch.setattr(os, "rename", failingRename)
        missing = asset((tmp_path / "missing.pt").as_uri(), name="missing", path="missing.pt")
        with pytest.raises(PluginServiceError):
            updater(writePluginZip(tmp_path / "v2.zip", "2.0", assets=assets + [missing]), tmp_path / "plugins").execute()
        monkeypatch.undo()
        assert (pluginFolder / "weights.pt").read_text() == "weights"

    def test_failedAssetListingRestoresPlugin(self, tmp_path, monkeypatch):
        """ An update failing before the installation of the new version puts the plugin back. """
        installer(writePluginZip(tmp_path / "v1.zip", "1.0"), tmp_path / "plugins").execute()
        pluginFolder = tmp_path / "plugins" / "myPlugin"

        def failingReusableAssets(*args):
            raise RuntimeError("Symlink loop")

        monkeypatch.setattr(PluginUpdater, "_reusableAssets", failingReusableAssets)
        with pytest.raises(RuntimeError):
            updater(writePluginZip(tmp_path / "v2.zip", "2.0"), tmp_path / "plugins").execute()
        assert lockVersion(pluginFolder) == "1.0"
        assert [p.name for p in (tmp_path / "plugins").iterdir()] == ["myPlugin"]

    def test_renamedPlugin(self, tmp_path):
        """ A plugin renamed by its new version is installed in its new folder, in place of the installed one. """
        weights = writeFile(tmp_path / "remote" / "weights.pt", "weights")
        assets = [asset(weights.as_uri(), sha256=sha256Of(weights))]
        installer(writePluginZip(tmp_path / "v1.zip", "1.0", assets=assets), tmp_path / "plugins").execute()
        writeFile(tmp_path / "plugins" / "myPlugin" / "user.txt", "user")

        weights.unlink()
        updater(writePluginZip(tmp_path / "v2.zip", "2.0", name="newName", assets=assets), tmp_path / "plugins",
                name="newName", installedName="myPlugin").execute()
        newFolder = tmp_path / "plugins" / "newName"
        assert [p.name for p in (tmp_path / "plugins").iterdir()] == ["newName"]
        assert lockVersion(newFolder) == "2.0"
        assert (newFolder / "weights.pt").read_text() == "weights"
        assert (newFolder / "user.txt").read_text() == "user"

    def test_cancel(self, tmp_path):
        """ A cancelled update leaves the installed plugin in place. """
        installer(writePluginZip(tmp_path / "v1.zip", "1.0"), tmp_path / "plugins").execute()
        with pytest.raises(PluginServiceCancelled):
            updater(writePluginZip(tmp_path / "v2.zip", "2.0"), tmp_path / "plugins").execute(isCancelled=lambda: True)
        assert lockVersion(tmp_path / "plugins" / "myPlugin") == "1.0"
