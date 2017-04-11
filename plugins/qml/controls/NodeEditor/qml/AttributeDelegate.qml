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
            property variant plug: modelData
            property bool acceptableDrop: false
            anchors.centerIn: parent
            width: 10
            height: 10

            onEntered: {
                // Filter out inacceptable drops
                if( drag.source.objectName != draggable.objectName  // not an attribute connector
                   || root.node === drag.source.node                // same node
                   || root.isInput === drag.source.isInput )        // same type (in/out) of attribute
                {
                    drag.accepted = false;
                }
                acceptableDrop = drag.accepted
            }

            onExited: acceptableDrop = false;

            onDropped: {
                acceptableDrop = false;
                var obj = {};
                obj["source"] = drag.source.node.name;
                obj["target"] = root.node.name;
                obj["plug"] = plug.name;
                currentScene.graph.addEdge(obj)
            }

            Rectangle {
                anchors.centerIn: parent
                width: 10
                height: 10
                radius: 5
                color: "#5BB1F7"
                border.color: "white"
                opacity: dropArea.containsDrag && dropArea.acceptableDrop ? 1 : 0
                Behavior on opacity { NumberAnimation {}}
            }
        }

        Rectangle {
            id: draggable
            objectName: "attributeConnector"
            property alias isInput: root.isInput
            property alias node: root.node
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
                onReleased: parent.Drag.drop()
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
            thickness: 1
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
