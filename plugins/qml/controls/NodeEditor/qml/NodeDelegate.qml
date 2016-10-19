import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.2
import NodeEditor 1.0

Rectangle {

    id: root

    // dynamic properties
    property variant nodeModel : modelData
    property variant inputs: model.inputs
    property variant outputs: model.outputs
    QtObject {
        id: _p
        property int attributeHeight: 15
        property int attributeSpacing: 2
    }

    // properties
    z: currentNodeID == index ? 2 : 1
    radius: 10
    implicitWidth: 100
    implicitHeight: Math.max(inputs.count, outputs.count)
                    * (_p.attributeHeight + _p.attributeSpacing)
                    + title.height + radius
    color: Qt.rgba(0.1, 0.1, 0.1, 0.8)
    border.color: getColor()

    // functions
    function getInputItem(id) { return inputRepeater.itemAt(id) }
    function getOutputItem(id) { return outputRepeater.itemAt(id) }
    function getColor() {
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

    // slots & behaviors
    Component.onCompleted: { x = model.x; y = model.y; }
    onXChanged: { model.x = x; nodeMoved(root, model.modelData); }
    onYChanged: { model.y = y; nodeMoved(root, model.modelData); }
    Behavior on border.color { ColorAnimation {} }

    // mouse area
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        drag.target: root
        drag.axis: Drag.XAndYAxis
        propagateComposedEvents: true
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        onClicked: {
            if(mouse.button & Qt.RightButton) {
                nodeRightClicked(root, model.modelData);
                return;
            }
            currentNodeID = index;
            nodeLeftClicked(root, model.modelData)
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.topMargin: 4
            anchors.bottomMargin: 4
            spacing: 4

            // node title
            Label {
                id: title
                Layout.fillWidth: true
                text: model.type
                horizontalAlignment: Text.AlignHCenter
                state: "xsmall"
                color: root.border.color
            }

            // node attributes
            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true
                RowLayout {
                    anchors.fill: parent
                    spacing: _p.attributeSpacing
                    ColumnLayout {
                        Repeater {
                            id: inputRepeater
                            model: root.inputs
                            AttributeDelegate {
                                Layout.maximumHeight: _p.attributeHeight
                                isInput: true
                            }
                        }
                        Item { Layout.fillHeight: true } // spacer
                    }
                    ColumnLayout {
                        Repeater {
                            id: outputRepeater
                            model: root.outputs
                            AttributeDelegate {
                                Layout.maximumHeight: _p.attributeHeight
                                isInput: false
                            }
                        }
                        Item { Layout.fillHeight: true } // spacer
                    }
                }
            }
        }
    }

}
