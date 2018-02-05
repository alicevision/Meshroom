import QtQuick 2.9
import QtQuick.Layouts 1.3
import QtQuick.Controls 2.2
import MaterialIcons 2.2

/**
  A component to display and edit a Node's attributes.
*/
ColumnLayout {
    id: root

    property variant node: null  // the node to edit
    property bool readOnly: false

    spacing: 0

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
                text: MaterialIcons.settings
                font.family: MaterialIcons.fontFamily
                onClicked: settingsMenu.popup()
                checkable: true
                checked: settingsMenu.visible
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

    StackLayout {
        Layout.fillHeight: true
        Layout.fillWidth: true

        currentIndex: tabBar.currentIndex

        Item {

            ListView {
                id: attributesListView

                anchors.fill: parent
                anchors.margins: 4

                clip: true
                spacing: 1
                ScrollBar.vertical: ScrollBar { id: scrollBar }

                model: node ? node.attributes : undefined

                delegate: AttributeItemDelegate {
                    labelWidth: 180
                    width: attributesListView.width
                    attribute: object
                }
            }
        }

        NodeLog {
            id: nodeLog

            Layout.fillHeight: true
            Layout.fillWidth: true
            node: root.node

        }
    }
    TabBar {
        id: tabBar

        Layout.fillWidth: true
        width: childrenRect.width
        position: TabBar.Footer
        TabButton {
            text: "Attributes"
            width: implicitWidth
            padding: 4
            leftPadding: 8
            rightPadding: leftPadding
        }
        TabButton {
            text: "Log"
            width: implicitWidth
            leftPadding: 8
            rightPadding: leftPadding
        }
    }
}
