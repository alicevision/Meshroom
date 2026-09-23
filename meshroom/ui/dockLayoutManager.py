import json
import logging

from PySide6.QtCore import QObject, QPoint, QSettings, Signal, Slot, Property
from PySide6.QtGui import QGuiApplication

from meshroom.ui.dockLayout import DockLayout, LEGACY_VISIBILITY_SETTINGS, applyLegacySettings


class DockLayoutManager(QObject):
    """
    Exposes the layout of the dockable panels (see `meshroom.ui.dockLayout`) to QML, and keeps it in
    the application settings so that it is restored at the next start.

    Layouts can also be saved as named workspaces, stored in the settings as well. The "Default"
    workspace is built in: loading it resets the layout.

    It outlives the QML engine reloads (e.g. on a palette change): the QML side rebuilds the layout
    from it whenever it is (re)created.
    """

    settingsGroup = "UILayout"
    layoutKey = "dockLayout"
    workspacesKey = "workspaces"
    defaultWorkspaceName = "Default"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = DockLayout()
        self._restore()
        self._clampFloatingWindows()

    def _clampFloatingWindows(self):
        """ Make sure the floating windows are visible on the current screens, which may have changed. """
        if QGuiApplication.instance():
            screens = [screen.availableGeometry() for screen in QGuiApplication.screens()]
            self._layout.clampFloatingGeometries([[g.x(), g.y(), g.width(), g.height()] for g in screens])

    def _restore(self):
        """ Load the layout from the settings, or build it from the settings of older versions. """
        settings = QSettings()
        settings.beginGroup(self.settingsGroup)
        data = settings.value(self.layoutKey)
        if data:
            try:
                if self._layout.load(json.loads(data)):
                    return
            except (TypeError, ValueError):
                pass
            logging.warning("Invalid layout of the panels in the settings, the default one is used.")
            return
        legacySettings = {key: settings.value(key) for key in LEGACY_VISIBILITY_SETTINGS if settings.contains(key)}
        applyLegacySettings(self._layout, legacySettings)

    def _save(self):
        settings = QSettings()
        settings.beginGroup(self.settingsGroup)
        settings.setValue(self.layoutKey, json.dumps(self._layout.toDict()))

    def _structureChanged(self):
        self._save()
        self.layoutChanged.emit()
        self.openPanelsChanged.emit()

    @Slot(str, str, str, int, result=bool)
    def movePanel(self, panelId, groupId, zone, index):
        """
        Move a panel next to a group of tabs (see `DockLayout.movePanel`).

        Returns:
            bool: whether the layout changed.
        """
        if not self._layout.movePanel(panelId, groupId, zone, index):
            return False
        self._structureChanged()
        return True

    @Slot(str, bool)
    def setPanelOpen(self, panelId, isOpen):
        """ Open or close a panel. An opened panel becomes the current tab of its group. """
        if isOpen:
            self.raisePanel(panelId)
        elif self._layout.setPanelOpen(panelId, False):
            self._save()
            self.openPanelsChanged.emit()

    @Slot(str)
    def raisePanel(self, panelId):
        """ Open a panel if needed and make it the current tab of its group. """
        group = self._layout.groupOf(panelId)
        if not group:
            return
        opened = self._layout.setPanelOpen(panelId, True)
        raised = self._layout.setCurrent(group["id"], panelId)
        if opened or raised:
            self._save()
        if opened:
            self.openPanelsChanged.emit()
        # Always notify, the QML group may have a different current tab than the layout while the
        # panel is closed
        self.currentPanelChanged.emit(group["id"], panelId)

    @Slot(str, result=bool)
    def canFloat(self, panelId):
        """ Whether a panel can be displayed in a floating window. """
        return self._layout.canFloat(panelId)

    @Slot(str, int, int, int, int, result=bool)
    def floatPanel(self, panelId, x, y, width, height):
        """
        Move a panel to a new floating window with the given geometry.

        Returns:
            bool: whether the layout changed; it does not if the panel cannot float, or is already alone
            in a floating window.
        """
        if not self._layout.floatPanel(panelId, [x, y, width, height]):
            return False
        self._clampFloatingWindows()
        self._structureChanged()
        return True

    @Slot(str, result=bool)
    def dockPanel(self, panelId):
        """ Move a panel from a floating window back to the main window (see `DockLayout.dockPanel`). """
        if not self._layout.dockPanel(panelId):
            return False
        self._structureChanged()
        return True

    @Slot(str, int, int, int, int)
    def setFloatingGeometry(self, windowId, x, y, width, height):
        """ Store the geometry of a floating window, as moved or resized by the user. """
        if self._layout.setFloatingGeometry(windowId, [x, y, width, height]):
            self._save()

    @Slot(str)
    def closeFloatingWindow(self, windowId):
        """ Close the panels of a floating window, which is hidden until one of them is reopened. """
        if self._layout.closeFloatingWindow(windowId):
            self._save()
            self.openPanelsChanged.emit()

    @Slot(str, str)
    def setCurrent(self, groupId, panelId):
        """ Store the current tab of a group, as selected by the user. """
        if self._layout.setCurrent(groupId, panelId):
            self._save()
            self.currentPanelChanged.emit(groupId, panelId)

    @Slot(str, "QVariantList", result="QVariantList")
    def setSizes(self, splitId, sizes):
        """
        Store the sizes of the children of a split, as resized by the user (see `DockLayout.setSizes`).

        Returns:
            list: the new sizes as fractions, or an empty list if they could not be applied.
        """
        fractions = self._layout.setSizes(splitId, sizes)
        if fractions is None:
            return []
        self._save()
        return fractions

    def _workspaces(self):
        """ Return the saved workspaces: their layouts by name. """
        settings = QSettings()
        settings.beginGroup(self.settingsGroup)
        try:
            workspaces = json.loads(settings.value(self.workspacesKey) or "{}")
        except (TypeError, ValueError):
            workspaces = None
        return workspaces if isinstance(workspaces, dict) else {}

    def _setWorkspaces(self, workspaces):
        settings = QSettings()
        settings.beginGroup(self.settingsGroup)
        settings.setValue(self.workspacesKey, json.dumps(workspaces))
        self.workspacesChanged.emit()

    @Slot(str, result=bool)
    def saveWorkspace(self, name):
        """
        Save the current layout as a workspace, replacing any workspace with the same name.

        Returns:
            bool: whether it was saved; the name must not be empty nor the one of the default workspace.
        """
        name = name.strip()
        if not name or name.lower() == self.defaultWorkspaceName.lower():
            return False
        workspaces = self._workspaces()
        workspaces[name] = self._layout.toDict()
        self._setWorkspaces(workspaces)
        return True

    @Slot(str, result=bool)
    def loadWorkspace(self, name):
        """
        Replace the current layout with a saved workspace, or with the default layout for the default one.

        Returns:
            bool: whether the workspace was loaded.
        """
        if name == self.defaultWorkspaceName:
            self._layout.reset()
        else:
            data = self._workspaces().get(name)
            if data is None or not self._layout.load(data):
                logging.warning(f"Cannot load the workspace '{name}'.")
                return False
            self._clampFloatingWindows()
        self._structureChanged()
        return True

    @Slot(str)
    def deleteWorkspace(self, name):
        workspaces = self._workspaces()
        if workspaces.pop(name, None) is not None:
            self._setWorkspaces(workspaces)

    @Slot(str, result=bool)
    def hasWorkspace(self, name):
        """ Whether a workspace with this name exists, the default one included. """
        name = name.strip()
        return name.lower() == self.defaultWorkspaceName.lower() or name in self._workspaces()

    @Slot(int, int, result=QObject)
    def windowAt(self, x, y):
        """ Return the top level window at the given global position, or None. """
        return QGuiApplication.topLevelAt(QPoint(x, y))

    layoutChanged = Signal()
    # Current layout: changes when panels are moved, not when they are opened, closed or resized
    layout = Property("QVariantMap", lambda self: self._layout.toDict(), notify=layoutChanged)
    openPanelsChanged = Signal()
    openPanels = Property("QVariantList", lambda self: self._layout.openPanels(), notify=openPanelsChanged)
    panelIds = Property("QVariantList", lambda self: self._layout.panelIds, constant=True)
    # Emitted with the ids of a group and of the panel that became its current tab
    currentPanelChanged = Signal(str, str)
    workspacesChanged = Signal()
    # Name of the built-in workspace holding the default layout
    defaultWorkspace = Property(str, lambda self: self.defaultWorkspaceName, constant=True)
    # Names of the saved workspaces, the default one excluded
    workspaceNames = Property("QVariantList", lambda self: sorted(self._workspaces(), key=str.lower), notify=workspacesChanged)
