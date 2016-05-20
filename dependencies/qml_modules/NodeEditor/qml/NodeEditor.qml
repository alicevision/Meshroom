import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0
import NodeEditor 1.0

Rectangle {

    id: root

    // properties
    property variant nodes: null
    property variant connections: null
    property Component nodeModel: NodeModel {}
    property Component connectionModel: ConnectionModel {}
    property int currentNodeID: 0

    // signals
    signal nodeMoved(var node)
    signal nodeLeftClicked(var node)
    signal nodeRightClicked(var node)

    // slots
    onNodeMoved: canvas.requestPaint()

    // functions
    function init() {
        if(root.nodes) root.nodes.destroy();
        if(root.connections) root.connections.destroy();
        root.nodes = root.nodeModel.createObject();
        root.connections = root.connectionModel.createObject();
        canvas.requestPaint();
    }

    function fitLayout() {
        if(!root.nodes)
            return;
        var xmargin = 40;
        var ymargin = 20;
        var yoffset = 60;
        for(var i=0; i<root.nodes.count; i++)
        {
            var nodeItem = repeater.itemAt(i);
            nodeItem.x = xmargin + i*(nodeItem.width + 20);
            nodeItem.y = yoffset; // + Math.random() * 60 - 60;
        }
        canvas.requestPaint();
    }

    function drawConnections(context) {
        if(!root.connections)
            return;
        for(var i=0; i<root.connections.count; i++)
        {
            var connection = root.connections.get(i);
            var sourceNodeID = root.nodes.getID(connection.source);
            var targetNodeID = root.nodes.getID(connection.target);
            var targetInputs = root.nodes.get(targetNodeID).inputs;
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
    color: Style.window.color.dark
    Image {
        anchors.fill: parent
        source: "qrc:///images/stripes.png"
        fillMode: Image.Tile
        opacity: 0.3
        MouseArea {
            anchors.fill: parent
            onClicked: selectionChanged(null)
        }
    }

    // draw nodes
    Repeater {
        id: repeater
        anchors.fill: parent
        model: root.nodes
        delegate: NodeDelegate {
            width: 100
            height: 60
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
    Text {
        visible: !root.nodes || root.nodes.count == 0
        anchors.centerIn: parent
        text: "Add new nodes with [TAB]"
        color: Style.text.color.xdark
    }
}
