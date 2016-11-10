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
    signal nodeItemMoved(var item, var node, var pos)
    signal nodeLeftClicked(var item, var node, var pos)
    signal nodeRightClicked(var item, var node, var pos)
    signal edgeLeftClicked(var item, var edge, var pos)
    signal edgeRightClicked(var item, var edge, var pos)

    onNodeItemMoved: {
        var o = node.serializeToJSON()
        o['x'] = Math.round(item.x);
        o['y'] = Math.round(item.y);
        root.graph.moveNode(o)
    }

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
                id: nodeRepeater
                model: root.graph ? root.graph.nodes : 0
                delegate: NodeDelegate {}
            }
            Repeater {
                id: edgeRepeater
                model: root.graph.edges
                delegate: EdgeItem {
                    id: edgeItem
                    property int sourceId: root.graph.nodes.rowIndex(modelData.source)
                    property int targetId: root.graph.nodes.rowIndex(modelData.target)
                    property int sourceAttrID: 0
                    property int targetAttrID: targetNode.inputs.rowIndex(modelData.plug)
                    sourceNode: nodeRepeater.itemAt(sourceId)
                    sourceAttr: sourceNode.getOutputAnchor(sourceAttrID)
                    targetNode: nodeRepeater.itemAt(targetId)
                    targetAttr: targetNode.getInputAnchor(targetAttrID)
                    scaleFactor: parent.scale
                    color: containsMouse ? "#5BB1F7" : "#CCC"
                    onReleased: {
                        switch(mouse.button) {
                            case Qt.LeftButton:
                                root.edgeLeftClicked(edgeItem, modelData, Qt.point(mouse.x, mouse.y))
                                break;
                            case Qt.RightButton:
                                root.edgeRightClicked(edgeItem, modelData, Qt.point(mouse.x, mouse.y))
                                break;
                        }
                    }
                }
            }
        }
    }
}
