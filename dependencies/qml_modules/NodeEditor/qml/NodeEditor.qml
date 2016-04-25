import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0

Rectangle {

    id: root

    // properties
    property variant nodeModel: _nodes
    property variant connectionModel: null

    // signal/slots
    signal nodeChanged()
    signal selectionChanged(var node)
    onNodeChanged: canvas.requestPaint()
    Component.onCompleted: {
        if(!root.nodeModel)
            return;
        fitLayout();
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

    // main functions
    function drawConnections(context) {
        if(!root.connectionModel)
            return;
        for(var i=0; i<root.connectionModel.count; i++)
        {
            var sourceNodeId = root.connectionModel.get(i).source_node;
            var targetNodeId = root.connectionModel.get(i).target_node;
            var targetSlotId = root.connectionModel.get(i).target_slot;
            var sourceNodeItem = repeater.itemAt(sourceNodeId);
            var targetNodeItem = repeater.itemAt(targetNodeId);
            var sourceNode = root.nodeModel.get(sourceNodeId);
            var targetNode = root.nodeModel.get(targetNodeId);
            drawConnection(context, sourceNodeItem.getOutputItem(0), targetNodeItem.getInputItem(targetSlotId));
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
    function fitLayout() {
        if(!root.nodeModel)
            return;
        var xmargin = 40;
        var ymargin = 20;
        var yoffset = 60;
        for(var i=0; i<root.nodeModel.count; i++)
        {
            var nodeItem = repeater.itemAt(i);
            nodeItem.x = xmargin + i*(nodeItem.width + 20);
            nodeItem.y = yoffset;// + Math.random() * 60 - 60;
        }
        canvas.requestPaint();
    }

    // draw nodes
    Repeater {
        id: repeater
        anchors.fill: parent
        model: root.nodeModel
        delegate: NodeDelegate {
            width: 80
            height: 50
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

    Text {
        visible: !root.nodeModel || root.nodeModel.count == 0
        anchors.centerIn: parent
        text: "Add new nodes with [TAB]"
        color: Style.text.color.xdark
    }
}
