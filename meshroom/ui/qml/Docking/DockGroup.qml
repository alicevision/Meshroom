import QtQuick
import QtQuick.Controls

import MaterialIcons 2.2

/**
 * DockGroup displays the panels of a "tabs" node of the dock layout as tabs, the contextual toolbar of
 * the current panel being displayed on the right of the tabs.
 *
 * A tab can be dragged onto another group (or onto another place of the same group) to move its
 * panel: the DockManager then shows where the panel would be dropped, see dropZoneAt().
 */

Item {
    id: root

    /// "tabs" node of the dock layout
    property var node
    property DockManager manager
    /// The DockArea displaying the group
    property Item area

    /// Ids of the open panels of the group, in tab order
    readonly property var openPanelIds: {
        var open = manager.layoutModel.openPanels
        return node.panels.filter(function(panelId) { return open.indexOf(panelId) !== -1 })
    }
    /// Id of the current tab, which may be a closed panel
    property string currentPanelId: node.current
    /// Id of the displayed panel: the current one, or the first open one if the current one is closed
    readonly property string displayedPanelId: openPanelIds.indexOf(currentPanelId) !== -1 ? currentPanelId : (openPanelIds.length > 0 ? openPanelIds[0] : "")
    readonly property DockPanel displayedPanel: displayedPanelId ? manager.panels[displayedPanelId] : null
    /// Whether the group has been replaced by a rebuild of the layout and waits for its destruction
    property bool retired: false

    /// Where the dragged panel would be dropped on this group, if it is the target of a drag
    readonly property var dropTarget: manager.dropTarget && manager.dropTarget.group === root ? manager.dropTarget : null

    visible: openPanelIds.length > 0

    Component.onCompleted: manager.registerGroup(root)
    Component.onDestruction: manager.unregisterGroup(root)

    Connections {
        target: root.manager.layoutModel
        function onCurrentPanelChanged(groupId, panelId) {
            if (groupId === root.node.id)
                root.currentPanelId = panelId
        }
    }

    /// Display the panels of the node in the group
    function hostPanels() {
        node.panels.forEach(function(panelId) {
            var panel = manager.panels[panelId]
            panel.parent = content
            panel.anchors.fill = content
            panel.dockGroup = root
            panel.visible = Qt.binding(function() { return root.displayedPanelId === panelId })
        })
        updateToolBar()
    }

    /// Return the tab of an open panel of the group, or null
    function tabItem(panelId) {
        for (var i = 0; i < tabRepeater.count; ++i) {
            var tab = tabRepeater.itemAt(i)
            if (tab && tab.panelId === panelId)
                return tab
        }
        return null
    }

    /// Make a panel the current tab of the group
    function selectPanel(panelId) {
        currentPanelId = panelId
        manager.layoutModel.setCurrent(node.id, panelId)
    }

    /**
     * Return where a panel dragged at (x, y), in the group coordinates, would be dropped:
     * - over the tabs, as a new tab before the tab under the cursor ("center" zone, with an index),
     * - over the center of the content, as the last tab ("center" zone, index -1),
     * - over the borders of the content, beside the group ("left", "right", "top" or "bottom" zone).
     */
    function dropZoneAt(x, y) {
        if (y < header.height) {
            var index = node.panels.length
            for (var i = 0; i < tabRepeater.count; ++i) {
                var tab = tabRepeater.itemAt(i)
                if (x < tab.x + tab.width / 2) {
                    index = node.panels.indexOf(tab.panelId)
                    break
                }
            }
            return { "group": root, "zone": "center", "index": index }
        }
        var u = x / width
        var v = (y - header.height) / content.height
        if (u > 0.3 && u < 0.7 && v > 0.3 && v < 0.7)
            return { "group": root, "zone": "center", "index": -1 }
        // The side closest to the cursor
        var distances = [u, 1 - u, v, 1 - v]
        var zone = ["left", "right", "top", "bottom"][distances.indexOf(Math.min.apply(null, distances))]
        return { "group": root, "zone": zone, "index": -1 }
    }

    QtObject {
        id: m
        property Item toolBar: null
        property DockPanel toolBarOwner: null
        readonly property color paneBackgroundColor: Qt.darker(root.palette.window, 1.15)
        property string contextMenuPanelId
    }

    onDisplayedPanelChanged: updateToolBar()

    function updateToolBar() {
        if (retired)
            return
        var toolBar = displayedPanel ? displayedPanel.toolBar : null
        if (m.toolBar && m.toolBar !== toolBar && m.toolBar.parent === toolBarHost)
            m.toolBarOwner.parkToolBar()
        m.toolBar = toolBar
        m.toolBarOwner = displayedPanel
        if (toolBar)
            toolBar.parent = toolBarHost
    }

    Rectangle {
        id: header
        width: parent.width
        height: 28
        color: m.paneBackgroundColor
        clip: true

        Row {
            id: tabRow
            x: 4
            y: 4
            height: parent.height - y
            spacing: 2

            Repeater {
                id: tabRepeater
                model: root.openPanelIds

                delegate: Rectangle {
                    id: tab

                    readonly property string panelId: modelData
                    readonly property DockPanel panel: root.manager.panels[panelId]
                    readonly property bool displayed: panelId === root.displayedPanelId

                    // The room of the close button is kept when it is hidden, so the tabs do not move
                    width: Math.min(tabLabel.implicitWidth + closeButton.width, 300)
                    height: tabRow.height
                    color: displayed ? root.palette.window : Qt.darker(root.palette.window, 1.30)
                    border.color: Qt.darker(root.palette.window, 1.50)
                    border.width: displayed ? 0 : 1

                    Label {
                        id: tabLabel
                        anchors.fill: parent
                        anchors.rightMargin: closeButton.width
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        leftPadding: 8
                        rightPadding: 2
                        text: tab.panel.tabTitle
                        textFormat: Text.StyledText
                        elide: Text.ElideRight
                    }

                    MouseArea {
                        id: tabMouseArea
                        anchors.fill: parent
                        acceptedButtons: Qt.LeftButton | Qt.RightButton
                        hoverEnabled: true

                        property point pressPosition
                        property bool dragging: false

                        onPressed: function(mouse) {
                            pressPosition = Qt.point(mouse.x, mouse.y)
                            if (mouse.button === Qt.LeftButton)
                                root.selectPanel(tab.panelId)
                        }
                        onPositionChanged: function(mouse) {
                            if (!(mouse.buttons & Qt.LeftButton))
                                return
                            var globalPosition = mapToGlobal(mouse.x, mouse.y)
                            if (!dragging && Math.max(Math.abs(mouse.x - pressPosition.x), Math.abs(mouse.y - pressPosition.y)) >= Qt.styleHints.startDragDistance) {
                                dragging = true
                                root.manager.draggedPanel = tab.panel
                            }
                            if (dragging)
                                root.manager.updateDrag(globalPosition.x, globalPosition.y)
                        }
                        onReleased: function(mouse) {
                            if (dragging) {
                                dragging = false
                                var globalPosition = mapToGlobal(mouse.x, mouse.y)
                                root.manager.endDrag(globalPosition.x, globalPosition.y)
                            } else if (mouse.button === Qt.RightButton) {
                                m.contextMenuPanelId = tab.panelId
                                tabContextMenu.popup(tab, mouse.x, mouse.y)
                            }
                        }
                        onCanceled: {
                            if (dragging) {
                                dragging = false
                                root.manager.cancelDrag()
                            }
                        }
                    }

                    // Above the MouseArea, so that pressing it does not start a drag of the tab
                    MaterialToolButton {
                        id: closeButton
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        padding: 2
                        font.pointSize: 8
                        text: MaterialIcons.close
                        // On the current tab and on the hovered one, like in most tabbed interfaces
                        opacity: tab.displayed || tabMouseArea.containsMouse || hovered ? 1 : 0
                        enabled: opacity > 0
                        ToolTip.text: "Close " + tab.panel.title + " (reopen it from the View menu)"
                        onClicked: root.manager.layoutModel.setPanelOpen(tab.panelId, false)
                    }
                }
            }
        }

        // Toolbar of the displayed panel
        Row {
            id: toolBarHost
            anchors.right: parent.right
            anchors.rightMargin: 2
            anchors.verticalCenter: parent.verticalCenter
        }
    }

    Item {
        id: content
        anchors.top: header.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
    }

    Menu {
        id: tabContextMenu

        readonly property bool floating: root.area !== root.manager.mainArea

        MenuItem {
            text: "Float"
            // A panel alone in a floating window already floats
            enabled: root.manager.layoutModel.canFloat(m.contextMenuPanelId)
                     && !(tabContextMenu.floating && root.manager.panelsOf(root.area.rootNode).length === 1)
            onTriggered: {
                var position = root.mapToGlobal(0, 0)
                root.manager.floatPanel(root.manager.panels[m.contextMenuPanelId], position.x + 30, position.y + 30)
            }
        }
        MenuItem {
            text: "Dock in Main Window"
            enabled: tabContextMenu.floating
            onTriggered: root.manager.layoutModel.dockPanel(m.contextMenuPanelId)
        }
        MenuSeparator {}
        MenuItem {
            text: "Close"
            onTriggered: root.manager.layoutModel.setPanelOpen(m.contextMenuPanelId, false)
        }
    }

    // Where the dragged panel would be dropped
    Rectangle {
        id: dropHighlight
        visible: root.dropTarget !== null
        z: 10
        color: Qt.rgba(root.palette.highlight.r, root.palette.highlight.g, root.palette.highlight.b, 0.25)
        border.color: root.palette.highlight
        border.width: 2

        readonly property string zone: root.dropTarget ? root.dropTarget.zone : ""
        readonly property bool onTabs: root.dropTarget !== null && zone === "center" && root.dropTarget.index >= 0
        readonly property real tabInsertX: {
            if (!onTabs)
                return 0
            var tab = root.tabItem(root.node.panels[root.dropTarget.index])
            return tab ? tab.x + tabRow.x : tabRow.x + tabRow.width
        }

        // Over the tabs: a marker where the tab would be inserted
        x: onTabs ? tabInsertX - 1 : (zone === "right" ? content.width / 2 : 0)
        y: onTabs ? 2 : (zone === "bottom" ? content.y + content.height / 2 : content.y)
        width: onTabs ? 3 : (zone === "left" || zone === "right" ? content.width / 2 : content.width)
        height: onTabs ? header.height - 4 : (zone === "top" || zone === "bottom" ? content.height / 2 : content.height)
    }
}
