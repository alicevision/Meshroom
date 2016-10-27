import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.2
import NodeEditor 1.0

RowLayout {
    id: root

    property var node
    property bool isInput: true
    property alias edgeAnchor: _edgeAnchor

    spacing: 2
    Label {
        Layout.fillWidth: true
        text: model.name
        horizontalAlignment: Text.AlignRight
        state: "xsmall"
        visible: !isInput
    }
    Rectangle {
        Layout.fillHeight: true
        Layout.preferredWidth: 1
        color: Qt.rgba(1, 1, 1, 0.5)
        DropArea {
            id: dropArea
            property variant node: root.node
            property variant plug: modelData
            anchors.centerIn: parent
            width: 10
            height: 10
            onDropped: drop.accept()

            Rectangle {
                anchors.centerIn: parent
                width: 10
                height: 10
                radius: 5
                color: "#5BB1F7"
                border.color: "white"
                opacity: dropArea.containsDrag && isInput ? 1 : 0
                Behavior on opacity { NumberAnimation {}}
            }
        }

        Rectangle {
            id: draggable
            anchors.centerIn: dragArea.pressed ? undefined : parent
            width: 10
            height: 10
            radius: 5
            color: "transparent"
            opacity: dragArea.containsMouse ? 1 : 0
            Behavior on opacity { NumberAnimation {}}
            border.color: "white"
            Drag.active: dragArea.drag.active
            Drag.hotSpot.x: width*0.5
            Drag.hotSpot.y: height*0.5
            visible: !isInput

            MouseArea {
                id: dragArea
                anchors.fill: parent
                anchors.margins: drag.active ? -50 : 0
                hoverEnabled: true
                drag.target: parent
                drag.threshold: 0
                onReleased: {
                    if(drag.active && parent.Drag.target)
                    {
                        var targetNode = parent.Drag.target.node;
                        var targetPlug = parent.Drag.target.plug;
                        var result = parent.Drag.drop();
                        if(result != Qt.IgnoreAction) {
                            var obj = {}
                            obj["source"] = root.node.name;
                            obj["target"] = targetNode.name;
                            obj["plug"] = targetPlug.name;
                            currentScene.graph.addEdge(obj)
                        }
                    }
                }
            }
            Item {
                id: draggableEdgeAnchor
                anchors.verticalCenter: parent.verticalCenter
            }
        }
        Item {
            id: _edgeAnchor
            anchors.centerIn: parent
        }
        // Temporary edge for use when connecting nodes
        EdgeItem {
            sourceNode: _edgeAnchor
            sourceAttr: _edgeAnchor
            targetNode: draggable
            targetAttr: draggableEdgeAnchor
            visible: dragArea.drag.active
        }
    }
    Label {
        Layout.fillWidth: true
        text: model.name
        horizontalAlignment: Text.AlignLeft
        state: "xsmall"
        visible: isInput
    }
}
