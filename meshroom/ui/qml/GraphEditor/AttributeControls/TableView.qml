import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

import MaterialIcons 2.2

ColumnLayout {
    id: root
    spacing: 0
    property bool editable: true
    required property var attribute
    property bool expanded: false

    CollapsibleListHeader {
        elementCount: root.attribute.value.count
        editable: root.editable
        expanded: root.expanded
        onExpandToggled: root.expanded = !root.expanded
        onAddRequested: _currentScene.appendAttribute(root.attribute, undefined)

        ToolButton {
            text: MaterialIcons.fullscreen
            font.family: MaterialIcons.fontFamily
            font.pointSize: 11
            padding: 2
            ToolTip.text: "Open in fullscreen"
            ToolTip.visible: hovered
            onClicked: {
                fullscreenWindow.width = fullscreenBody.preferredContentWidth
                fullscreenWindow.height = fullscreenBody.preferredContentHeight
                fullscreenWindow.show()
            }
        }
    }

    // Holds its own TableViewBody instance (rather than reparenting the inline one), so
    // the table can be displayed in fullscreen and inline at the same time; both stay in
    // sync since they're bound to the same underlying `attribute`.
    Window {
        id: fullscreenWindow
        title: attribute
               ? attribute.label
               : ""
        palette: root.palette
        color: palette.window

        TableViewBody {
            id: fullscreenBody
            anchors.fill: parent
            attribute: root.attribute
            editable: root.editable
            isFullscreen: true
        }
    }

    TableViewBody {
        id: inlineBody
        Layout.fillWidth: true
        visible: root.expanded
        Layout.preferredHeight: root.expanded
                                ? Math.min(totalTableHeight + 40, 330)
                                : 0
        attribute: root.attribute
        editable: root.editable
    }
}

