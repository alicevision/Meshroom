import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.2


RowLayout {

    property bool isInput: true

    Layout.maximumHeight: 15
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
            property variant node: nodeModel
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
            anchors.centerIn: parent
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
                hoverEnabled: true
                anchors.fill: parent
                drag.target: parent
                drag.threshold: 0
                onPressed: {
                    draggable.anchors.centerIn = undefined;
                    var globalCoordinates = mapToItem(canvas, mouse.x, mouse.y);
                    var vector = Qt.vector2d(globalCoordinates.x-mouse.x*0.5, globalCoordinates.y-mouse.y*0.5)
                    newEdgeStarted(nodeModel, modelData, vector);
                }
                onPositionChanged: {
                    if(!drag.active)
                        return;
                    var globalCoordinates = mapToItem(canvas, mouse.x, mouse.y);
                    var vector = Qt.vector2d(globalCoordinates.x-mouse.x*0.5, globalCoordinates.y-mouse.y*0.5)
                    newEdgeMoved(nodeModel, modelData, vector);
                }
                onReleased: {
                    if(!drag.active)
                        return;
                    draggable.anchors.centerIn = draggable.parent;
                    var globalCoordinates = mapToItem(canvas, mouse.x, mouse.y);
                    var vector = Qt.vector2d(globalCoordinates.x-mouse.x*0.5, globalCoordinates.y-mouse.y*0.5)
                    if(parent.Drag.target) {
                        var targetNode = parent.Drag.target.node;
                        var targetPlug = parent.Drag.target.plug;
                        var result = parent.Drag.drop();
                        if(result != Qt.IgnoreAction) {
                            newEdgeFinished(targetNode, targetPlug, vector);
                            return;
                        }
                    }
                    newEdgeFinished(null, null, vector);
                }
            }
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
