# coding:utf-8

from pathlib import Path

from meshroom.env import meshroomFolder
from meshroom.core.plugins import getLocalPluginsFolder, initLocalPluginsFolder, meshroomRegistriesFolder
from ..utils import writeFile


def test_shippedRegistries():
    # Fails if the registries folder is moved/renamed or its files stop being tracked
    assert (meshroomRegistriesFolder / "meshroomHub.json").is_file()


def test_seedsRegistries(tmp_path):
    registries = tmp_path / "registries"
    writeFile(registries / "hub.json", "{}")
    writeFile(registries / "notARegistry.txt")
    pluginsFolder = tmp_path / "install" / "plugins"

    initLocalPluginsFolder(pluginsFolder, registries)

    assert sorted(p.name for p in pluginsFolder.iterdir()) == ["hub.json"]


def test_existingFolderUntouched(tmp_path):
    registries = tmp_path / "registries"
    writeFile(registries / "hub.json", "{}")
    pluginsFolder = tmp_path / "plugins"
    initLocalPluginsFolder(pluginsFolder, registries)

    # A registry removed by the user is not restored on the next run
    (pluginsFolder / "hub.json").unlink()
    initLocalPluginsFolder(pluginsFolder, registries)

    assert not (pluginsFolder / "hub.json").exists()


def test_localPluginsFolderPath(tmp_path, monkeypatch):
    monkeypatch.delenv("MESHROOM_INSTALL_DIR", raising=False)
    monkeypatch.delenv("MESHROOM_LOCAL_PLUGINS_PATH", raising=False)
    assert getLocalPluginsFolder() == Path(meshroomFolder).parent / "plugins"

    monkeypatch.setenv("MESHROOM_LOCAL_PLUGINS_PATH", str(tmp_path))
    assert getLocalPluginsFolder() == tmp_path
