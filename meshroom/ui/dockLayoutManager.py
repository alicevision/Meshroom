import json
import logging

from PySide6.QtCore import QObject, QPoint, QSettings, Signal, Slot, Property
from PySide6.QtGui import QGuiApplication

from meshroom.ui.dockLayout import DockLayout, LEGACY_VISIBILITY_SETTINGS, applyLegacySettings


class DockLayoutManager(QObject):
    """
    Exposes the layout of the dockable panels (see `meshroom.ui.dockLayout`) to QML, and keeps it in
    the application settings so that it is restored at the next start.

    It outlives the QML engine reloads (e.g. on a palette change): the QML side rebuilds the layout
    from it whenever it is (re)created.
    """

    settingsGroup = "UILayout"
    layoutKey = "dockLayout"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = DockLayout()
        self._restore()

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
