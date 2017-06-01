import QtQuick 2.7
import QtQuick.Layouts 1.3
import QtQuick.Controls 2.1
import FontAwesome 1.0
import Meshroom.Scene 1.0
import Meshroom.TemplateCollection 1.0
import "controls"

Item {
    id: root
    anchors.fill: parent
    anchors.margins: 1

    state: "NEW"
    states: [
        State {
            name: "NEW"
            PropertyChanges { target: stackLayout; currentIndex: 0 }
        },
        State {
            name: "RECENT"
            PropertyChanges { target: stackLayout; currentIndex: 1 }
        },
        State {
            name: "SETTINGS"
            PropertyChanges { target: stackLayout; currentIndex: 2 }
        }
    ]

    RowLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillHeight: true
            implicitWidth: 150
            color: "#252525"
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 2
                Label {
                    state: "large"
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "Meshroom"
                    font.bold: true
                }
                Label {
                     text: "1.0.0"
                     state: "xsmall"
                     enabled: false
                     anchors.horizontalCenter: parent.horizontalCenter
                }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.margins: 6
                    implicitHeight: 1
                    color: "#555"
                }

                Column {
                    width: parent.width
                    ToolButton {
                        id: button_new
                        text: FontAwesome.plusCircle + " New"
                        font.family: FontAwesome.fontFamily
                        width: parent.width
                        checked: root.state == "NEW"
                        onClicked: root.state = "NEW"
                    }
                    ToolButton {
                        id: button_recent
                        text: FontAwesome.clockO + " Recent"
                        font.family: FontAwesome.fontFamily
                        width: parent.width
                        checked: root.state == "RECENT"
                        onClicked: root.state = "RECENT"
                    }
                    ToolButton {
                        id: button_settings
                        text: FontAwesome.cogs + " Settings"
                        font.family: FontAwesome.fontFamily
                        width: parent.width
                        checkable: false
                        checked: root.state == "SETTINGS"
                        onClicked: root.state = "SETTINGS"
                    }
                }

                Item { Layout.fillHeight: true }

            }
        }


        StackLayout {
            id: stackLayout

            Item {
                id: newSceneLayout
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: false

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 6

                    TemplateManager {
                        scene: _application.templateScene
                    }

                    GridLayout {
                        Layout.margins: 10
                        Layout.alignment: Qt.AlignCenter

                        columns: 2

                        TextField {
                            id: graphNameTF
                            placeholderText: "Name"
                        }

                        CheckBox {
                            id: addToCurrentScene
                            text: "Add to current Scene"
                            enabled: !!_application.scene.url.toString().trim()
                            checked: enabled
                        }

                        Button {
                            Layout.columnSpan: 2
                            Layout.alignment: Qt.AlignHCenter

                            text: FontAwesome.plusCircle + (addToCurrentScene.checked ? " Create  " : " Create and Open  ")
                            font.family: FontAwesome.fontFamily
                            enabled: graphNameTF.text.trim() != ""
                            onClicked: {
                                if(addToCurrentScene.checked)
                                {
                                    _application.createTemplateGraph(graphNameTF.text.trim());
                                    graphNameTF.text = "";
                                    return;
                                }

                                _window.newScene()
                                var dialog = _dialogs.saveScene.createObject(_window.contentItem,
                                                                             {
                                                                              // TODO: add folder path
                                                                              "currentFile": graphNameTF.text.trim(),
                                                                             });
                                dialog.file = graphNameTF.text.trim()
                                dialog.onAccepted.connect(function() {
                                    // TODO: handle errors
                                    _application.createTemplateScene(graphNameTF.text, dialog.file);
                                    graphNameTF.text = ""
                                });
                                dialog.open();
                            }
                        }
                    }
                }
            }

            Item {
                id: recentScenesLayout
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: false
                clip: true

                GridView {
                    id: recentScenes_gridView
                    anchors.fill: parent
                    anchors.margins: 6

                    cellWidth: 160
                    cellHeight: 130
                    ScrollIndicator.vertical: ScrollIndicator {}

                    model: _application.settings.recentFiles
                    delegate: Item {
                        width: recentScenes_gridView.cellWidth
                        height: recentScenes_gridView.cellHeight

                        Rectangle {
                            anchors.fill: parent
                            anchors.margins: 4
                            color: ma.containsMouse ? Qt.lighter("#1F8699", 1.2) : "#1F8699"
                            Label {
                                text: FontAwesome.cube
                                state: "large"
                                anchors.centerIn: parent
                                font.family: FontAwesome.fontFamily
                            }

                            Label {
                                id: name
                                text: modelData.toString().split("/").pop().replace(".meshroom", "")
                                width: parent.width
                                elide: Text.ElideRight
                                horizontalAlignment: Text.AlignHCenter
                                anchors.bottom: parent.bottom
                                state: "small"
                                padding: 5
                                background: Rectangle {
                                    color: "#222"
                                    width: name.width
                                    height: name.height
                                    opacity: 0.8
                                }
                            }
                        }
                        MouseArea {
                            id: ma
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            ToolTip.visible: containsMouse
                            ToolTip.text: modelData.toString().replace("file://", "")
                            onClicked: _application.loadScene(modelData)
                        }
                    }
                }
            }
        }
    }
}
