import QtQuick 2.9
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import Qt.labs.settings 1.0
import Utils 1.0
import MaterialIcons 2.2
import GraphEditor 1.0


/// Meshroom "Preferences" window
Dialog {
    id: root

    property string currentNode: ""

    x: parent.width / 2 - width / 2
    y: parent.height / 2 - height / 2
    width: parent.width * 0.5
    height: parent.height * 0.5

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

    Column {
        anchors.fill: parent
        TabBar {
            id: tabBar

            TabButton {
                text: "General"
            }

            TabButton {
                text: "Node Default Attribute Value Overrides"
                width: implicitWidth
            }
        }

        Rectangle {
            color: Qt.darker(activePalette.window, 1.15)
            width: parent.width
            height: parent.height - tabBar.height
            StackLayout {
                currentIndex: tabBar.currentIndex
                anchors.fill: parent

                // General settings
                Column {
                    Settings {
                        category: "General"
                        property alias defaultPalette: defaultPaletteCB.currentIndex
                    }
                    Grid {
                        columns: 2
                        columnSpacing: 10
                        padding: columnSpacing
                        verticalItemAlignment: Grid.AlignVCenter
                        Label {
                            text: "Default Palette"
                        }
                        ComboBox {
                            id: defaultPaletteCB
                            model: ["Dark", "Light"]
                        }
                    }
                }

                // Node default attribute overrides
                Row {
                    anchors.fill: parent
                    Column {
                        width: parent.width / 2
                        height: parent.height
                        Label {
                            id: nodesListLabel
                            text: "Nodes"
                            padding: 5
                        }
                        MaterialToolButton {
                            id: nodeOverrideAddButton
                            text: MaterialIcons.add
                            width: parent.width
                            onClicked: addNodeMenu.popup()
                            Menu {
                                id: addNodeMenu
                                Repeater {
                                    model: _preferences.unusedNodes
                                    delegate: MenuItem {
                                        text: modelData
                                        font.pointSize: 8
                                        padding: 3
                                        onClicked: {
                                            root.currentNode = modelData
                                            _preferences.addNodeOverride(modelData)
                                        }
                                    }
                                }
                            }
                        }
                        ListView {
                            width: parent.width
                            height: parent.height - nodesListLabel.height - nodeOverrideAddButton.height
                            model: Object.keys(_preferences.attributeOverrides)
                            clip: true
                            ScrollBar.vertical: ScrollBar { id: nodesScrollBar }
                            
                            delegate: Rectangle {
                                property string node: modelData
                                color: root.currentNode == modelData ? activePalette.highlight : nodeListMA.containsMouse || nodeOverrideRemoveButton.hovered ? activePalette.mid : "transparent"
                                width: parent.width - nodesScrollBar.width
                                height: 25
                                Label {
                                    text: parent.node
                                    padding: 5
                                }
                                MouseArea {
                                    id: nodeListMA
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    onClicked: root.currentNode = parent.node
                                }
                                MaterialToolButton {
                                    id: nodeOverrideRemoveButton
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
                        width: parent.width / 2
                        height: parent.height
                        Label {
                            id: attributesListLabel
                            text: "Attributes"
                            padding: 5
                        }
                        MaterialToolButton {
                            id: attributeOverrideAddButton
                            text: MaterialIcons.add
                            width: parent.width
                            onClicked: addAttributeMenu.popup()
                            Menu {
                                id: addAttributeMenu
                                Repeater {
                                    model: _preferences.getUnusedAttributes(root.currentNode, _preferences.attributeOverrides)
                                    delegate: MenuItem {
                                        text: modelData.name
                                        font.pointSize: 8
                                        padding: 3
                                        onClicked: {
                                            _preferences.addAttributeOverride(root.currentNode, modelData.name, modelData.value)
                                        }
                                    }
                                }
                            }
                        }
                        ListView {
                            width: parent.width
                            height: parent.height - attributesListLabel.height - attributeOverrideAddButton.height
                            spacing: 2
                            clip: true
                            ScrollBar.vertical: ScrollBar { id: attributesScrollBar }
                            model: _preferences.attributeOverrides[root.currentNode]
                            delegate: Row {
                                width: parent.width - attributesScrollBar.width
                                height: AttributeItemDelegate.height
                                AttributeItemDelegate {
                                    width: parent.width - attributeOverrideRemoveButton.width
                                    labelWidth: 180
                                    attribute: object
                                    onValueChanged: _preferences.addAttributeOverride(root.currentNode, object.name, value)
                                }
                                MaterialToolButton {
                                    id: attributeOverrideRemoveButton
                                    text: MaterialIcons.remove
                                    onClicked: _preferences.removeAttributeOverride(root.currentNode, object.name)
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
