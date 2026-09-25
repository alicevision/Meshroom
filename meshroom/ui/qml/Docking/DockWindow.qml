import QtQuick
import QtQuick.Controls

/**
 * DockWindow is a floating window displaying a part of the dock layout in its own DockArea. It is
 * created by the DockManager for each floating window of the layout.
 *
 * It must be transient for the main window: the shortcuts of the main window then keep working while
 * it is active.
 */

ApplicationWindow {
    id: root

    /// The DockManager (untyped to avoid a cyclic dependency between the types)
    property var manager
    /// Floating window of the dock layout: {id, geometry, root}
    property var entry
    readonly property Item area: dockArea

    readonly property var openPanels: manager.panelsOf(entry.root).filter(function(panelId) { return manager.openPanelSet[panelId] === true })

    title: openPanels.map(function(panelId) { return manager.panels[panelId].title }).join(", ")
    // The window is hidden, not destroyed, when its panels are closed: it keeps its place in the layout
    visible: openPanels.length > 0
    minimumWidth: 200
    minimumHeight: 150

    onClosing: function(close) {
        // Closing the window closes its panels, which hides it
        close.accepted = false
        manager.layoutModel.closeFloatingWindow(entry.id)
    }

    onXChanged: geometryTimer.restart()
    onYChanged: geometryTimer.restart()
    onWidthChanged: geometryTimer.restart()
    onHeightChanged: geometryTimer.restart()

    // Store the geometry once the window stopped moving or being resized
    Timer {
        id: geometryTimer
        interval: 500
        onTriggered: {
            if (root.visible)
                root.manager.layoutModel.setFloatingGeometry(root.entry.id, root.x, root.y, root.width, root.height)
        }
    }

    DockArea {
        id: dockArea
        anchors.fill: parent
        manager: root.manager
    }
}
