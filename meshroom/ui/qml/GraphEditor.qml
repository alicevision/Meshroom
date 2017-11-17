import QtQuick 2.7
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

/**
  A component displaying a Graph (nodes, attributes and edges).
*/
Item {
    id: root

    property variant graph: null

    property variant selectedNode: null

    property int nodeWidth: 140
    property int nodeHeight: 40
    property int gridSpacing: 10
    property var _attributeToDelegate: ({})

    // signals
    signal workspaceMoved()
    signal workspaceClicked()

    clip: true

    SystemPalette { id: palette }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        property double factor: 1.15
        // Activate multisampling for edges antialiasing
        layer.enabled: true
        layer.samples: 8

        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
        drag.threshold: 0
        onWheel: {
            var zoomFactor = wheel.angleDelta.y > 0 ? factor : 1/factor
            if(Math.min(draggable.width*draggable.scale*zoomFactor, draggable.height*draggable.scale*zoomFactor) < 10)
                return
            var point = mapToItem(draggable, wheel.x, wheel.y)
            draggable.x += (1-zoomFactor) * point.x * draggable.scale
            draggable.y += (1-zoomFactor) * point.y * draggable.scale
            draggable.scale *= zoomFactor
            draggable.scale = draggable.scale.toFixed(2)
            workspaceMoved()
        }

        onPressed: {
            if(mouse.button & Qt.MiddleButton)
                drag.target = draggable // start drag
        }
        onReleased: {
            drag.target = undefined // stop drag
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

            // Edges
            Repeater {
                id: edgesRepeater

                // delay edges loading after nodes (edges needs attribute pins to be created)
                model: nodeRepeater.loaded ? root.graph.edges : undefined

                delegate: Edge {
                    property var src: root._attributeToDelegate[edge.src]
                    property var dst: root._attributeToDelegate[edge.dst]
                    property var srcAnchor: src.nodeItem.mapFromItem(src, src.edgeAnchorPos.x, src.edgeAnchorPos.y)
                    property var dstAnchor: dst.nodeItem.mapFromItem(dst, dst.edgeAnchorPos.x, dst.edgeAnchorPos.y)

                    edge: object
                    color: containsMouse ? palette.highlight : palette.text
                    opacity: 0.7
                    point1x: src.nodeItem.x + srcAnchor.x
                    point1y: src.nodeItem.y + srcAnchor.y
                    point2x: dst.nodeItem.x + dstAnchor.x
                    point2y: dst.nodeItem.y + dstAnchor.y
                    onPressed: {
                        if(event.button == Qt.RightButton)
                            _reconstruction.removeEdge(edge)
                    }
                }
            }

            // Nodes
            Repeater {
                id: nodeRepeater

                model: root.graph.nodes
                property bool loaded: count === model.count
                onLoadedChanged: if(loaded) { doAutoLayout() }

                delegate: Node {
                    node: object
                    width: root.nodeWidth

                    onAttributePinCreated: registerAttributePin(attribute, pin)

                    onPressed: {
                        root.selectedNode = object
                    }

                    Behavior on x {
                        NumberAnimation {}
                    }
                    Behavior on y {
                        NumberAnimation {}
                    }
                }
            }
        }
    }

    Row {
        anchors.bottom: parent.bottom

        Button {
            text: "Fit"
            onClicked: root.fit()
            z: 10
        }

        Button {
            text: "Layout"
            onClicked: root.doAutoLayout()
            z: 10
        }
    }

    function registerAttributePin(attribute, pin)
    {
        root._attributeToDelegate[attribute] = pin
    }

    // Fit graph to fill root
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

    // Really basic auto-layout based on node depths
    function doAutoLayout()
    {
        var grid = new Array(nodeRepeater.count)
        for(var i=0; i< nodeRepeater.count; ++i)
            grid[i] = new Array(nodeRepeater.count)
        for(var i=0; i<nodeRepeater.count; ++i)
        {
            var obj = nodeRepeater.itemAt(i);
        }

        for(var i=0; i<nodeRepeater.count; ++i)
        {
            var obj = nodeRepeater.itemAt(i);
            var j=0;
            while(1)
            {
                if(grid[obj.node.depth][j] == undefined)
                {
                    grid[obj.node.depth][j] = obj;
                    break;
                }
                j++;
            }
        }
        for(var x= 0; x<nodeRepeater.count; ++x)
        {
            for(var y=0; y<nodeRepeater.count; ++y)
            {
                if(grid[x][y] != undefined)
                {
                    grid[x][y].x = x * (root.nodeWidth + root.gridSpacing)
                    grid[x][y].y = y * (root.nodeHeight + root.gridSpacing)
                }
            }
        }
    }
}
