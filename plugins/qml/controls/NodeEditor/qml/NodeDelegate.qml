import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.2
import NodeEditor 1.0

Rectangle {

    id: root

    // dynamic properties
    property variant node: modelData
    property variant inputs: model.inputs
    property variant outputs: model.outputs
    QtObject {
        id: _p
        property int attributeHeight: 15
        property int attributeSpacing: 2
    }

    // properties
    z: selectedNodeID == index ? 2 : 1
    radius: 10
    implicitWidth: 100
    implicitHeight: {
        if(!inputs || !outputs)
            return title.height + radius
        return Math.max(inputs.count, outputs.count)
                * (_p.attributeHeight + _p.attributeSpacing)
                + title.height + radius
    }
    color: Qt.rgba(0.1, 0.1, 0.1, 0.8)
    border.color: getColor()

    // functions
    function getInputAnchor(id) { return inputRepeater.itemAt(id).edgeAnchor }
    function getOutputAnchor(id) { return outputRepeater.itemAt(id).edgeAnchor }
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
    Connections {
        target: model.modelData
        onXChanged: if(Math.round(root.x) !== model.x) root.x = model.x;
        onYChanged: if(Math.round(root.y) !== model.y) root.y = model.y;
    }
    onXChanged: model.x = root.x
    onYChanged: model.y = root.y
    Behavior on border.color { ColorAnimation {} }

    // mouse area
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        drag.target: root
        drag.axis: Drag.XAndYAxis
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        onClicked: {
            if(mouse.button & Qt.RightButton) {
                nodeRightClicked(root, model.modelData);
                return;
            }
            selectedNodeID = index;
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
                text: model.name
                horizontalAlignment: Text.AlignHCenter
                state: "xsmall"
                color: root.border.color
            }
            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true
                RowLayout {
                    anchors.fill: parent
                    spacing: _p.attributeSpacing
                    // input attributes
                    ColumnLayout {
                        Repeater {
                            id: inputRepeater
                            model: root.inputs
                            AttributeDelegate {
                                Layout.maximumHeight: _p.attributeHeight
                                isInput: true
                                node: root.node
                            }
                        }
                        Item { Layout.fillHeight: true } // spacer
                    }
                    // output attributes
                    ColumnLayout {
                        Repeater {
                            id: outputRepeater
                            model: root.outputs
                            AttributeDelegate {
                                Layout.maximumHeight: _p.attributeHeight
                                isInput: false
                                node: root.node
                            }
                        }
                        Item { Layout.fillHeight: true } // spacer
                    }
                }
            }
        }
    }

}
