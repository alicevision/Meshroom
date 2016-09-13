import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3
import NodeEditor 1.0

Item {

    id: root

    // properties
    property variant graph: Graph {}
    property int currentNodeID: 0

    QtObject {
        id: _private
        property bool selectionEnabled: false
        property variant selection: []
    }

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
        _private.selection = []
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
            drawConnection(context, sourceNodeItem.getOutputItem(0), targetNodeItem.getInputItem(targetPlugID), connection.modelData);
        }
    }

    function drawConnection(context, itemA, itemB, connectionObj) {
        var outputPos = repeater.mapFromItem(itemA, itemA.width, itemA.height/2);
        var inputPos  = repeater.mapFromItem(itemB, 0, itemB.height/2);

        // calculate control points
        var curveScale = 0.7;
        var ctrlPtDist = Math.abs(inputPos.x - outputPos.x) * curveScale;
        var ctrlPtAX = outputPos.x + ctrlPtDist;
        var ctrlPtAY = outputPos.y;
        var ctrlPtBX = inputPos.x - ctrlPtDist;
        var ctrlPtBY = inputPos.y;

        // transparent mouse sensitive area
        var thickness = 8;
        context.strokeStyle = Qt.rgba(0, 0, 0, 0);
        context.lineWidth = 2;
        context.beginPath();
        context.moveTo(outputPos.x, outputPos.y-thickness);
        context.bezierCurveTo(ctrlPtAX, ctrlPtAY-thickness, ctrlPtBX, ctrlPtBY-thickness, inputPos.x, inputPos.y-thickness);
        context.lineTo(inputPos.x, inputPos.y+thickness);
        context.bezierCurveTo(ctrlPtBX, ctrlPtBY+thickness, ctrlPtAX, ctrlPtAY+thickness, outputPos.x, outputPos.y+thickness);
        context.closePath();
        context.stroke();

        // handle selection & stroke color
        context.strokeStyle = Qt.rgba(0.5, 0.5, 0.5, 1);
        if(_private.selectionEnabled && context.isPointInPath(mouseArea.mouseX, mouseArea.mouseY)) {
            context.strokeStyle = Qt.rgba(0.35, 0.69, 0.96, 1)
            // add to selection
            var index = _private.selection.indexOf(connectionObj);
            if(index<0)
                _private.selection.push(connectionObj);
        }

        // colored bezier curve
        context.beginPath();
        context.moveTo(outputPos.x, outputPos.y);
        context.bezierCurveTo(ctrlPtAX, ctrlPtAY, ctrlPtBX, ctrlPtBY, inputPos.x, inputPos.y);
        context.stroke();
        context.closePath();
    }

    Flickable {
        anchors.fill: parent
        ScrollBar.vertical: ScrollBar {}
        ScrollBar.horizontal: ScrollBar {}
        clip: true
        contentWidth: canvas.width
        contentHeight: canvas.height
        // draw connections
        Canvas {
            id: canvas
            width: 1000
            height: 600
            onPaint: {
                if(!context)
                    getContext("2d");
                context.clearRect(0, 0, width, height);
                drawConnections(context);
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
        // mouse area
        MouseArea {
            id: mouseArea
            anchors.fill: parent
            hoverEnabled: true
            onClicked: selectionChanged(null)
            onPositionChanged: {
                _private.selectionEnabled = (mouse.modifiers & Qt.ShiftModifier);
                refresh();
            }
            // onPressed: {
            //     console.log("selection:")
            //     for(var i = 0; i<_private.selection.length; ++i)
            //         console.log("-", _private.selection[i].source, ">", _private.selection[i].target, "::", _private.selection[i].plug)
            // }
        }
    }

    // help msg
    Label {
        anchors.centerIn: parent
        visible: !root.graph.nodes || root.graph.nodes.count == 0
        text: "Add new nodes with [TAB]"
    }
}
