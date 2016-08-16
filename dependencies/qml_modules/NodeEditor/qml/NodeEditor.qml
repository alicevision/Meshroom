import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3
import NodeEditor 1.0

Item {

    id: root

    // properties
    property variant graph: Graph {}
    property int currentNodeID: 0

    // signals
    signal nodeMoved(var node)
    signal nodeLeftClicked(var node)
    signal nodeRightClicked(var node)

    // slots
    onNodeMoved: refresh()
    Connections {
        target: root.graph.nodes
        onCountChanged: refresh()
    }
    Connections {
        target: root.graph.connections
        onCountChanged: refresh()
    }

    function refresh() {
        canvas.requestPaint();
    }

    function fitLayout() {
        if(!root.graph.nodes)
            return;
        var xmargin = 40;
        var ymargin = 20;
        var yoffset = 60;
        for(var i=0; i<root.graph.nodes.count; i++)
        {
            var nodeItem = repeater.itemAt(i);
            nodeItem.x = xmargin + i*(nodeItem.width + 20);
            nodeItem.y = yoffset; // + Math.random() * 60 - 60;
        }
        refresh();
    }

    function drawConnections(context) {
        if(!root.graph.connections)
            return;
        for(var i=0; i<root.graph.connections.count; i++)
        {
            var connection = root.graph.connections.get(i);
            var sourceNodeID = root.graph.nodes.getID(connection.source);
            var targetNodeID = root.graph.nodes.getID(connection.target);
            var targetInputs = root.graph.nodes.get(targetNodeID).inputs;
            var targetPlugID = targetInputs.getID(connection.plug);
            if(sourceNodeID<0 || targetNodeID<0 || targetPlugID<0)
                continue;
            var sourceNodeItem = repeater.itemAt(sourceNodeID);
            var targetNodeItem = repeater.itemAt(targetNodeID);
            drawConnection(context, sourceNodeItem.getOutputItem(0), targetNodeItem.getInputItem(targetPlugID));
        }
    }

    function drawConnection(context, itemA, itemB) {
        var outputPos = repeater.mapFromItem(itemA, itemA.width, itemA.height/2);
        var inputPos  = repeater.mapFromItem(itemB, 0, itemB.height/2);
        // calculate control points
        var curveScale = 0.7;
        var ctrlPtDist = Math.abs(inputPos.x - outputPos.x) * curveScale;
        var ctrlPtAX = outputPos.x + ctrlPtDist;
        var ctrlPtAY = outputPos.y;
        var ctrlPtBX = inputPos.x - ctrlPtDist;
        var ctrlPtBY = inputPos.y;
        // draw bezier curve
        context.strokeStyle = Qt.rgba(0.5, 0.5, 0.5, 1);
        context.lineWidth = 1;
        context.beginPath();
        context.moveTo(outputPos.x, outputPos.y);
        context.bezierCurveTo(ctrlPtAX, ctrlPtAY, ctrlPtBX, ctrlPtBY, inputPos.x, inputPos.y);
        context.stroke();
    }

    // background
    Rectangle {
        anchors.fill: parent
        color: Qt.rgba(0.5, 0.5, 0.5, 0.1)
        Image {
            anchors.fill: parent
            source: "qrc:///images/stripes.png"
            fillMode: Image.Tile
            opacity: 0.5
            MouseArea {
                anchors.fill: parent
                onClicked: selectionChanged(null)
            }
        }
    }

    // draw nodes
    Repeater {
        id: repeater
        anchors.fill: parent
        model: root.graph.nodes
        delegate: NodeDelegate {
            width: 100
            height: 80
        }
    }

    // draw connections
    Canvas {
        id: canvas
        anchors.fill: parent
        onPaint: {
            if(!context)
                getContext("2d");
            context.clearRect(0, 0, width, height);
            drawConnections(context);
        }
    }

    // help msg
    Label {
        anchors.centerIn: parent
        visible: !root.graph.nodes || root.graph.nodes.count == 0
        text: "Add new nodes with [TAB]"
    }
}
