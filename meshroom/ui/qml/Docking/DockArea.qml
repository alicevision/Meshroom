import QtQuick
import QtQuick.Controls

/**
 * DockArea displays the root node of a dock layout (the whole content of a window) with DockNodes.
 *
 * It also holds a hidden parking item, where the DockManager puts the panels of the window while the
 * layout is rebuilt: a panel must never leave its window, not even for a moment, since the Qt3D
 * scene of the 3D viewer does not survive it.
 */

Item {
    id: root

    property DockManager manager
    /// Root node of the layout displayed in the area, set with setRootNode()
    property var rootNode: null
    readonly property Item parking: parkingItem
    /// Whether the area is the one of a floating window
    readonly property bool floating: manager !== null && root !== manager.mainArea

    /// Display a node, destroying the ones displayed so far: their panels must have been parked
    function setRootNode(node) {
        rootLoader.source = ""
        rootNode = node
        if (node)
            rootLoader.setSource(Qt.resolvedUrl("DockNode.qml"), { "node": node, "manager": manager, "area": root })
    }

    Component.onCompleted: manager.registerArea(root)
    Component.onDestruction: manager.unregisterArea(root)

    Loader {
        id: rootLoader
        anchors.fill: parent
    }

    Item {
        id: parkingItem
        visible: false
    }

    // Label following the cursor while a panel is dragged over the area
    Label {
        visible: root.manager.draggedPanel !== null && root.manager.ghostArea === root
        x: root.manager.ghostPosition.x + 12
        y: root.manager.ghostPosition.y + 12
        z: 1000
        padding: 4
        text: root.manager.draggedPanel ? root.manager.draggedPanel.tabTitle : ""
        textFormat: Text.StyledText
        background: Rectangle {
            color: root.palette.window
            border.color: root.palette.highlight
            opacity: 0.9
        }
    }
}
