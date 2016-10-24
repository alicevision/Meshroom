import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3
import NodeEditor 1.0

Item {

    id: root
    property variant graph: null
    property int selectedNodeID: -1

    // signals
    signal workspaceClicked()
    signal nodeLeftClicked(var item, var node)
    signal nodeRightClicked(var item, var node)

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        drag.target: draggable
        property double factor: 1.5
        hoverEnabled: true
        onWheel: {
            var zoomFactor = wheel.angleDelta.y > 0 ? factor : 1/factor
            if(Math.min(draggable.width*draggable.scale*zoomFactor, draggable.height*draggable.scale*zoomFactor) < 10)
                return
            var point = mapToItem(draggable, wheel.x, wheel.y)
            draggable.x += (1-zoomFactor) * point.x * draggable.scale
            draggable.y += (1-zoomFactor) * point.y * draggable.scale
            draggable.scale *= zoomFactor
        }
        onClicked: {
            root.selectedNodeID = -1
            workspaceClicked()
        }
        Item {
            id: draggable
            transformOrigin: Item.TopLeft
            width: 1000
            height: 1000
            Repeater {
                model: root.graph ? root.graph.nodes : 0
                delegate: NodeDelegate {}
            }
        }
    }
}
