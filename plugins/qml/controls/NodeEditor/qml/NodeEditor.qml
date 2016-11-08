import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3
import NodeEditor 1.0

Item {

    id: root
    property variant graph: null
    property int selectedNodeID: -1

    // signals
    signal workspaceMoved()
    signal workspaceClicked()
    signal nodeMoved(var item, var node, var pos)
    signal nodeLeftClicked(var item, var node, var pos)
    signal nodeRightClicked(var item, var node, var pos)
    signal edgeLeftClicked(var item, var edge, var pos)
    signal edgeRightClicked(var item, var edge, var pos)

    // functions
    function fit() {
        // compute bounding box
        var first = nodeRepeater.itemAt(0)
        var bbox = Qt.rect(first.x, first.y, 1, 1)
        for(var i=0; i<root.graph.nodes.count; ++i) {
            var item = nodeRepeater.itemAt(i)
            bbox.x = Math.min(bbox.x, item.x)
            bbox.y = Math.min(bbox.y, item.y)
            bbox.width = Math.max(bbox.width, item.x+item.width)
            bbox.height = Math.max(bbox.height, item.y+item.height)
        }
        bbox.width -= bbox.x
        bbox.height -= bbox.y
        // rescale
        draggable.scale = Math.min(root.width/bbox.width, root.height/bbox.height)
        // recenter
        draggable.x = bbox.x*draggable.scale*-1 + (root.width-bbox.width*draggable.scale)*0.5
        draggable.y = bbox.y*draggable.scale*-1 + (root.height-bbox.height*draggable.scale)*0.5
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
            workspaceMoved()
        }
        onClicked: {
            root.selectedNodeID = -1
            workspaceClicked()
        }
        onPositionChanged: {
            if(drag.active)
                workspaceMoved()
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
