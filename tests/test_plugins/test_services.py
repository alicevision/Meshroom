#!/usr/bin/env python
# coding:utf-8

import json

import pytest

from meshroom.core.plugins.record import PluginRecord
from meshroom.core.plugins.provider import ArchivePluginProvider
from meshroom.core.plugins.local.service import PluginServiceCancelled, PluginServiceError
from meshroom.core.plugins.local.installer import PluginInstaller
from meshroom.core.plugins.local.uninstaller import PluginUninstaller
from meshroom.core.plugins.local.updater import PluginUpdater
from ..utils import writeFile, writeZip


def writePluginZip(zipPath, version="1.0", name="myPlugin"):
    """ Write a plugin archive whose "meshroom/config.json" declares "name" and "version". """
    # Use the legacy "config.json" rather than a "pyproject.toml", which would trigger a "uv sync"
    # of the plugin's dependencies on installation.
    return writeZip(zipPath, {"root/meshroom/config.json": json.dumps({"name": name, "version": version})})


def installer(archive, pluginsPath, name="myPlugin"):
    """ Return a PluginInstaller for the plugin archive "archive". """
    record = PluginRecord(name, "1.0", "me", archive.as_uri())
    return PluginInstaller(ArchivePluginProvider(archive.as_uri()), record, pluginsPath=pluginsPath)


def updater(archive, pluginsPath, name="myPlugin"):
    """ Return a PluginUpdater for the plugin archive "archive". """
    record = PluginRecord(name, "2.0", "me", archive.as_uri())
    return PluginUpdater(ArchivePluginProvider(archive.as_uri()), record, pluginsPath=pluginsPath)


def lockVersion(pluginFolder):
    """ Return the version written in the "plugin.lock" of the plugin installed in "pluginFolder". """
    return json.loads((pluginFolder / "plugin.lock").read_text())["version"]


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

    def test_invalidName(self, tmp_path):
        """ A name that is not a plain folder name is rejected, and nothing is removed. """
        writeFile(tmp_path / "plugins" / "file.txt")
        with pytest.raises(PluginServiceError):
            PluginUninstaller("..", tmp_path / "plugins").execute()
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

    def test_cancel(self, tmp_path):
        """ A cancelled update leaves the installed plugin in place. """
        installer(writePluginZip(tmp_path / "v1.zip", "1.0"), tmp_path / "plugins").execute()
        with pytest.raises(PluginServiceCancelled):
            updater(writePluginZip(tmp_path / "v2.zip", "2.0"), tmp_path / "plugins").execute(isCancelled=lambda: True)
        assert lockVersion(tmp_path / "plugins" / "myPlugin") == "1.0"
