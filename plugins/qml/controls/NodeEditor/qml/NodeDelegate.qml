import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.2
import NodeEditor 1.0

Rectangle {

    id: root
    radius: 10
    z: currentNodeID == index ? 2 : 1
    color: Qt.rgba(0.1, 0.1, 0.1, 0.8)

    border.color: {
        if(mouseArea.containsMouse)
            return "#5BB1F7";
        switch(model.status)
        {
            case Node.READY: break;
            case Node.WAITING: return "grey";
            case Node.RUNNING: return "lightgrey";
            case Node.ERROR: return "red";
            case Node.DONE: return "green";
        }
        return Qt.rgba(1, 1, 1, 0.2);
    }

    // properties
    property variant inputs: model.inputs
    property variant outputs: model.outputs

    // functions
    function getInputItem(id) {
        return inputRepeater.itemAt(id);
    }
    function getOutputItem(id) {
        return outputRepeater.itemAt(id);
    }

    // slots & behaviors
    Component.onCompleted: { x = model.x; y = model.y; }
    onXChanged: { model.x = x; nodeMoved(model); }
    onYChanged: { model.y = y; nodeMoved(model); }
    Behavior on border.color { ColorAnimation {} }

    // mouse area
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        drag.target: root
        drag.axis: Drag.XAndYAxis
        drag.minimumX: 0
        drag.maximumX: root.parent.width - root.width
        drag.minimumY: 0
        drag.maximumY: root.parent.height - root.height
        propagateComposedEvents: true
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        onClicked: {
            if(mouse.button & Qt.RightButton) {
                nodeRightClicked(model);
                return;
            }
            currentNodeID = index;
            nodeLeftClicked(model)
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.topMargin: 4
            anchors.bottomMargin: 4
            spacing: 4

            // node title
            Label {
                Layout.fillWidth: true
                text: model.name
                horizontalAlignment: Text.AlignHCenter
                state: "xsmall"
            }

            // node attributes
            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true
                RowLayout {
                    anchors.fill: parent
                    spacing: 2

                    // input attributes
                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        spacing: 2
                        Repeater {
                            id: inputRepeater
                            model: root.inputs
                            RowLayout {
                                Layout.fillWidth: true
                                Layout.maximumHeight: 15
                                spacing: 2
                                Rectangle {
                                    Layout.fillHeight: true
                                    Layout.preferredWidth: 1
                                    color: Qt.rgba(1, 1, 1, 0.5)
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: model.name
                                    horizontalAlignment: Text.AlignLeft
                                    state: "xsmall"
                                }
                            }
                        }
                        Item { Layout.fillHeight: true } // spacer
                    }

                    // output attributes
                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        spacing: 2
                        Repeater {
                            id: outputRepeater
                            model: root.outputs
                            RowLayout {
                                Layout.fillWidth: true
                                Layout.maximumHeight: 15
                                spacing: 2
                                Label {
                                    Layout.fillWidth: true
                                    text: model.name
                                    horizontalAlignment: Text.AlignRight
                                    state: "xsmall"
                                }
                                Rectangle {
                                    Layout.fillHeight: true
                                    Layout.preferredWidth: 1
                                    color: Qt.rgba(1, 1, 1, 0.5)
                                }
                            }
                        }
                        Item { Layout.fillHeight: true } // spacer
                    }

                }
            }
        }
    }

}
