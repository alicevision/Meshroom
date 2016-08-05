import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0
import Meshroom.GL 1.0

Item {

    DropArea {
        anchors.fill: parent
        hideBackground: true
        Connections {
            target: _window
            onLoadAlembic: glview.setAlembicScene(Qt.resolvedUrl(file))
        }
        onDropped: glview.setAlembicScene(drop.urls[0])
        GLView {
            id: glview
            anchors.fill: parent
            MouseArea {
                id: mouseArea
                anchors.fill: parent
                onClicked: viewSettings.state = "closed"
                propagateComposedEvents: true
            }
            Rectangle {
                id: viewSettings
                onFocusChanged: console.log(focus)
                width: parent.width*0.3
                height: parent.height
                color: "transparent"
                state: "closed"
                states: [
                    State {
                        name: "opened"
                        PropertyChanges {
                            target: viewSettings
                            x: parent.width-width
                            color: Style.window.color.xdark
                        }
                        PropertyChanges {
                            target: viewScroll
                            opacity: 1
                        }
                        PropertyChanges {
                            target: mouseArea
                            enabled: true
                        }
                    },
                    State {
                        name: "closed"
                        PropertyChanges {
                            target: viewSettings
                            x: parent.width-viewSettingsButton.width
                            color: "transparent"
                        }
                        PropertyChanges {
                            target: viewScroll
                            opacity: 0
                        }
                        PropertyChanges {
                            target: mouseArea
                            enabled: false
                        }
                    }
                ]
                transitions: [
                    Transition {
                        NumberAnimation { properties: "x,y,opacity" }
                        ColorAnimation { properties: "color" }
                    }
                ]
                ScrollView {
                    id: viewScroll
                    anchors.fill: parent
                    anchors.margins: 5
                    ColumnLayout {
                        width: viewScroll.width
                        Text {
                            text: "show"
                        }
                        CheckBox {
                            text: "grid"
                            checked: glview.gridVisibility
                            onClicked: glview.setGridVisibility(checked)
                        }
                        CheckBox {
                            text: "axis"
                            checked: glview.gizmoVisibility
                            onClicked: glview.setGizmoVisibility(checked)
                        }
                        CheckBox {
                            text: "cameras"
                            checked: glview.cameraVisibility
                            onClicked: glview.setCameraVisibility(checked)
                        }
                        Rectangle { // spacer
                            Layout.fillWidth: true
                            Layout.preferredHeight: 1
                            color: Style.window.color.dark
                        }
                        Text {
                            text: "point size"
                        }
                        Slider {
                            Layout.fillWidth: true
                            onValueChanged: glview.setPointSize(value)
                            minimumValue: 0.1
                            maximumValue: 10
                            value: 1
                            stepSize: 0.1
                        }
                        Rectangle { // spacer
                            Layout.fillWidth: true
                            Layout.preferredHeight: 1
                            color: Style.window.color.dark
                        }
                        Text {
                            text: "camera scale"
                        }
                        Slider {
                            Layout.fillWidth: true
                            onValueChanged: glview.setCameraScale(value)
                            minimumValue: 0.1
                            maximumValue: 5
                            value: 1
                            stepSize: 0.1
                        }
                    }
                }
                ToolButton {
                    id: viewSettingsButton
                    anchors.left: parent.left
                    anchors.bottom: parent.bottom
                    iconSource: "qrc:///images/disk.svg"
                    onClicked: viewSettings.state = (viewSettings.state == "opened") ? "closed" : "opened"
                }
            }


        }
    }

}
