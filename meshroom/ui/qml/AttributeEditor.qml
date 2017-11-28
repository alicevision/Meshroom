import QtQuick 2.9
import QtQuick.Layouts 1.3
import QtQuick.Controls 2.2

/**
  A component to display and edit a Node's attributes.
*/
ColumnLayout {
    id: root

    property variant node: null  // the node to edit
    property bool readOnly: false

    spacing: 4

    SystemPalette { id: palette }

    Pane {
        Layout.fillWidth: true
        background: Rectangle { color: Qt.darker(palette.window, 1.15) }
        padding: 2
        RowLayout {
            width: parent.width

            Label {
                Layout.fillWidth: true
                elide: Text.ElideMiddle
                text: node.nodeType
                horizontalAlignment: Text.AlignHCenter
                padding: 6
            }

            ToolButton {
                text: "⚙"
                onClicked: settingsMenu.popup()
            }
        }
        Menu {
            id: settingsMenu
            MenuItem {
                text: "Open Cache Folder"
                onClicked: Qt.openUrlExternally("file://" + node.internalFolder)
                ToolTip.text: node.internalFolder
                ToolTip.visible: hovered
                ToolTip.delay: 500
            }
            MenuSeparator {}
            MenuItem {
                text: "Clear Submitted Status"
                onClicked: node.clearSubmittedChunks()
            }
        }
    }

    ListView {
        id: attributesListView

        Layout.fillHeight: true
        Layout.fillWidth: true
        Layout.margins: 4
        clip: true
        spacing: 4
        ScrollBar.vertical: ScrollBar { id: scrollBar }

        model: node ? node.attributes : undefined

        delegate: RowLayout {
            width: attributesListView.width
            spacing: 4

            Label {
                id: parameterLabel
                text: object.label
                Layout.preferredWidth: 180
                color: object.isOutput ? "orange" : palette.text
                elide: Label.ElideRight
                ToolTip.text: object.desc.description
                ToolTip.visible: parameterMA.containsMouse
                ToolTip.delay: 200
                MouseArea {
                    id: parameterMA
                    anchors.fill: parent
                    hoverEnabled: true
                }
            }

            AttributeItemDelegate {
                Layout.fillWidth: true
                Layout.rightMargin: scrollBar.width
                height: childrenRect.height
                attribute: object
                readOnly: root.readOnly
            }
        }
    }
}
