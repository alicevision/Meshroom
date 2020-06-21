import QtQuick 2.9
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import Utils 1.0
import MaterialIcons 2.2
import GraphEditor 1.0


/// Meshroom "Preferences" window
Dialog {
    id: root

    property string currentNode: ""

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
                Column {
                    MaterialToolButton {
                        text: MaterialIcons.add
                        onClicked: addNodeMenu.popup()
                        Menu {
                            id: addNodeMenu
                            Repeater {
                                model: _preferences.unusedNodes
                                delegate: MenuItem {
                                    text: modelData
                                    onClicked: {
                                        _preferences.addNodeOverride(modelData)
                                    }
                                }
                            }
                        }
                    }
                    ListView {
                        height: 600
                        width: 310
                        model: Object.keys(_preferences.attributeOverrides)
                        clip: true
                        ScrollBar.vertical: ScrollBar { id: nodesScrollBar }
                        
                        delegate: Rectangle {
                            property string node: modelData
                            color: nodeListMA.containsMouse || nodeListRemoveButton.hovered ? activePalette.highlight : root.currentNode == modelData ? activePalette.dark : activePalette.button
                            width: parent.width
                            height: 15
                            Label {
                                text: parent.node
                            }
                            MouseArea {
                                id: nodeListMA
                                anchors.fill: parent
                                hoverEnabled: true
                                onClicked: root.currentNode = parent.node
                            }
                            MaterialToolButton {
                                id: nodeListRemoveButton
                                text: MaterialIcons.remove
                                width: parent.height
                                height: width
                                anchors.right: parent.right
                                visible: nodeListMA.containsMouse || hovered
                                onClicked: _preferences.removeNodeOverride(parent.node)
                            }
                        }
                    }
                }

                Column {
                    MaterialToolButton {
                        text: MaterialIcons.add
                        onClicked: addAttributeMenu.popup()
                        Menu {
                            id: addAttributeMenu
                            Repeater {
                                model: _preferences.getUnusedAttributes(root.currentNode)
                                delegate: MenuItem {
                                    text: modelData.name
                                    onClicked: {
                                        _preferences.addAttributeOverride(root.currentNode, modelData.name, modelData.value)
                                    }
                                }
                            }
                        }
                    }
                    ListView {
                        height: 300
                        width: 310
                        spacing: 2
                        clip: true
                        ScrollBar.vertical: ScrollBar { id: attributesScrollBar }
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
}
