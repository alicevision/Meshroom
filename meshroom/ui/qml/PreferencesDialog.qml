import QtQuick 2.9
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import Utils 1.0
import MaterialIcons 2.2
import GraphEditor 1.0


/// Meshroom "Preferences" window
Dialog {
    id: root

    x: parent.width / 2 - width / 2
    y: parent.height / 2 - height / 2
    width: parent.width * 0.9
    height: parent.height * 0.9

    // Fade in transition
    enter: Transition {
        NumberAnimation { property: "opacity"; from: 0.0; to: 1.0 }
    }

    modal: true
    closePolicy: Dialog.CloseOnEscape | Dialog.CloseOnPressOutside
    padding: 30
    topPadding: 30

    property variant nodes: null
    property variant test: null

    property string currentNode: ""

    header: Pane {
        background: Item {}

        Label {
            text: "Preferences"
        }

        MaterialToolButton {
            text: MaterialIcons.close
            anchors.right: parent.right
            onClicked: root.close()
        }
    }

    ColumnLayout {
        TabBar {
            id: tabBar

            TabButton {
                text: "Node Defaults"
            }
        }

        StackLayout {
            currentIndex: tabBar.currentIndex
            
            Row {
                ListView {
                    height: 300
                    width: 310
                    model: Object.keys(_preferences.attributeOverrides)

                    delegate: Button {
                        text: modelData
                        onClicked: root.currentNode = modelData
                    }
                }

                ListView {
                    height: 300
                    width: 310
                    spacing: 2
                    clip: true
                    ScrollBar.vertical: ScrollBar { id: scrollBar }
                    model: _preferences.attributeOverrides[root.currentNode]
                    delegate: AttributeItemDelegate {
                        updatePreferences: true
                        nodeName: root.currentNode
                        width: 300
                        labelWidth: 100
                        attribute: modelData
                    }
                }
            }
        }
    }
}
