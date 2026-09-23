import json

import pytest
from PySide6.QtCore import QCoreApplication, QSettings

from meshroom.ui.dockLayoutManager import DockLayoutManager


@pytest.fixture
def settings(tmp_path):
    """ Redirect the application settings to a temporary file. """
    names = (QCoreApplication.organizationName(), QCoreApplication.applicationName())
    QCoreApplication.setOrganizationName("AliceVision")
    QCoreApplication.setApplicationName("MeshroomDockLayoutTest")
    QSettings.setDefaultFormat(QSettings.IniFormat)
    QSettings.setPath(QSettings.IniFormat, QSettings.UserScope, str(tmp_path))
    yield QSettings()
    QSettings.setDefaultFormat(QSettings.NativeFormat)
    QCoreApplication.setOrganizationName(names[0])
    QCoreApplication.setApplicationName(names[1])


def groupIdOf(manager, panelId):
    return manager._layout.groupOf(panelId)["id"]


def withoutIds(value):
    """ Return a copy of a layout without the ids of its nodes, which are regenerated on reset. """
    if isinstance(value, dict):
        return {key: withoutIds(v) for key, v in value.items() if key != "id"}
    if isinstance(value, list):
        return [withoutIds(v) for v in value]
    return value


def test_layoutIsRestoredAtTheNextStart(settings):
    manager = DockLayoutManager()
    assert manager.movePanel("taskManager", groupIdOf(manager, "graphEditor"), "right", -1)
    manager.setPanelOpen("imageGallery", False)

    restored = DockLayoutManager()
    assert restored.layout == manager.layout
    assert "imageGallery" not in restored.openPanels


def test_invalidStoredLayoutFallsBackToTheDefaultOne(settings):
    settings.setValue("UILayout/dockLayout", "{not json")
    manager = DockLayoutManager()
    assert manager.layout["main"]["type"] == "split"
    assert "graphEditor" in manager.openPanels


def test_legacySettingsAreMigrated(settings):
    settings.setValue("UILayout/showViewer3D", "false")
    settings.setValue("UILayout/showTextViewer", "true")
    manager = DockLayoutManager()
    assert "viewer3D" not in manager.openPanels
    assert "textViewer" in manager.openPanels


def test_signals(settings):
    manager = DockLayoutManager()
    received = []
    manager.layoutChanged.connect(lambda: received.append("layout"))
    manager.openPanelsChanged.connect(lambda: received.append("open"))
    manager.currentPanelChanged.connect(lambda groupId, panelId: received.append(panelId))

    manager.setPanelOpen("viewer3D", False)
    assert received == ["open"]
    received.clear()
    manager.raisePanel("textViewer")
    assert received == ["open", "textViewer"]
    received.clear()
    manager.movePanel("nodeEditor", groupIdOf(manager, "graphEditor"), "center", -1)
    assert received == ["layout", "open"]
    received.clear()
    # Moving a panel where it already is changes nothing
    assert not manager.movePanel("nodeEditor", groupIdOf(manager, "nodeEditor"), "center", -1)
    assert received == []


def test_setSizes(settings):
    manager = DockLayoutManager()
    rootId = manager.layout["main"]["id"]
    assert manager.setSizes(rootId, [300, 100]) == [0.75, 0.25]
    assert manager.setSizes(rootId, [300]) == []
    assert DockLayoutManager().layout["main"]["sizes"] == [0.75, 0.25]


def test_workspaces(settings):
    manager = DockLayoutManager()
    defaultLayout = manager.layout
    manager.movePanel("taskManager", groupIdOf(manager, "graphEditor"), "right", -1)
    movedLayout = manager.layout
    assert manager.saveWorkspace("  Compute ")
    assert manager.saveWorkspace("assembly")
    assert manager.workspaceNames == ["assembly", "Compute"]
    assert manager.hasWorkspace("Compute")
    assert json.loads(settings.value("UILayout/workspaces"))["Compute"] == movedLayout

    # The default workspace resets the layout
    assert manager.loadWorkspace(manager.defaultWorkspace)
    assert withoutIds(manager.layout) == withoutIds(defaultLayout)
    assert manager.loadWorkspace("Compute")
    assert manager.layout == movedLayout

    manager.deleteWorkspace("assembly")
    assert manager.workspaceNames == ["Compute"]
    assert not manager.loadWorkspace("assembly")
    assert manager.layout == movedLayout


def test_invalidWorkspaceNames(settings):
    manager = DockLayoutManager()
    assert not manager.saveWorkspace("  ")
    assert not manager.saveWorkspace("default")
    assert manager.hasWorkspace("Default")
    assert manager.workspaceNames == []


def test_invalidWorkspaceIsNotLoaded(settings):
    settings.setValue("UILayout/workspaces", json.dumps({"broken": {"version": 999}}))
    manager = DockLayoutManager()
    before = manager.layout
    assert not manager.loadWorkspace("broken")
    assert manager.layout == before
