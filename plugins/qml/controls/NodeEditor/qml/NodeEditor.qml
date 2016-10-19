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
        property variant edgeBegin: Qt.vector2d(0,0)
        property variant edgeEnd: Qt.vector2d(0,0)
        property variant edgeDescriptor: null
    }

    // signals
    signal nodeMoved(var item, var node)
    signal nodeLeftClicked(var item, var node)
    signal nodeRightClicked(var item, var node)
    signal edgeAdded(var descriptor)
    signal edgeRemoved(var edge)

    signal newEdgeStarted(var node, var plug, var pos)
    signal newEdgeMoved(var node, var plug, var pos)
    signal newEdgeFinished(var node, var plug, var pos)
    onNewEdgeStarted: initializeTmpEdge(node, plug, pos)
    onNewEdgeMoved: updateTmpEdge(node, plug, pos)
    onNewEdgeFinished: finalizeTmpEdge(node, plug, pos)

    // slots
    onNodeMoved: refresh()
    Connections {
        target: root.graph.nodes
        onCountChanged: refresh()
    }
    Connections {
        target: root.graph.edges
        onCountChanged: refresh()
    }

    // functions
    function initializeTmpEdge(node, plug, pos) {
        _private.edgeBegin = pos;
        _private.edgeEnd = pos;
        _private.edgeDescriptor = new Object();
        refresh();
    }
    function updateTmpEdge(node, plug, pos) {
        _private.edgeEnd = pos;
        _private.edgeDescriptor.source = node.name;
        refresh();
    }
    function finalizeTmpEdge(node, plug, pos) {
        if(node && plug) {
            // add edge
            _private.edgeDescriptor.plug = plug.key;
            _private.edgeDescriptor.target = node.name;
            edgeAdded(_private.edgeDescriptor);
        }
        // clear
        _private.edgeBegin = Qt.vector2d(0,0);
        _private.edgeEnd = Qt.vector2d(0,0);
        _private.edgeDescriptor = null;
        refresh();
    }
    function refresh() { canvas.requestPaint() }
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
    function drawEdges(context) {
        var edges = root.graph.edges;
        if(!edges)
            return;
        _private.selection = []
        for(var i=0; i<edges.count; i++)
        {
            var edge = edges.data(edges.index(i,0), EdgeCollection.ModelDataRole);
            var sourceID = edge.sourceID();
            var targetID = edge.targetID();
            var plugID = edge.plugID();
            var sourceItem = repeater.itemAt(sourceID);
            var targetItem = repeater.itemAt(targetID);
            if(!sourceItem || !targetItem)
                continue
            drawEdge(context, sourceItem.getOutputItem(0), targetItem.getInputItem(plugID), edge);
        }
    }
    function drawEdge(context, itemA, itemB, edgeDescriptor) {
        if(!itemA || !itemB || !edgeDescriptor)
            return;
        var outputPos = itemA.mapToItem(canvas, itemA.width, itemA.height/2);
        var inputPos  = itemB.mapToItem(canvas, 0, itemB.height/2);
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
            var index = _private.selection.indexOf(edgeDescriptor);
            if(index<0)
                _private.selection.push(edgeDescriptor);
        }
        // colored bezier curve
        context.beginPath();
        context.moveTo(outputPos.x, outputPos.y);
        context.bezierCurveTo(ctrlPtAX, ctrlPtAY, ctrlPtBX, ctrlPtBY, inputPos.x, inputPos.y);
        context.stroke();
        context.closePath();
    }
    function drawTmpEdge(context) {
        // calculate control points
        var curveScale = 0.7;
        var ctrlPtDist = Math.abs(_private.edgeBegin.x - _private.edgeEnd.x) * curveScale;
        var ctrlPtAX = _private.edgeBegin.x + ctrlPtDist;
        var ctrlPtAY = _private.edgeBegin.y;
        var ctrlPtBX = _private.edgeEnd.x - ctrlPtDist;
        var ctrlPtBY = _private.edgeEnd.y;
        // colored bezier curve
        context.strokeStyle = Qt.rgba(0.5, 0.5, 0.5, 1);
        context.lineWidth = 2;
        context.beginPath();
        context.moveTo(_private.edgeBegin.x, _private.edgeBegin.y);
        context.bezierCurveTo(ctrlPtAX, ctrlPtAY, ctrlPtBX, ctrlPtBY, _private.edgeEnd.x, _private.edgeEnd.y);
        context.stroke();
        context.closePath();
    }

    // help msg
    Label {
        anchors.centerIn: parent
        visible: !root.graph.nodes || root.graph.nodes.count == 0
        text: "Add new nodes with [TAB]"
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        drag.target: draggable
        property double factor: 1.5
        hoverEnabled: true
        onClicked: selectionChanged(null)
        onWheel: {
            var zoomFactor = wheel.angleDelta.y > 0 ? factor : 1/factor
            if(Math.min(draggable.width*draggable.scale*zoomFactor, draggable.height*draggable.scale*zoomFactor) < 10)
                return
            var point = mapToItem(draggable, wheel.x, wheel.y)
            draggable.x += (1-zoomFactor) * point.x * draggable.scale
            draggable.y += (1-zoomFactor) * point.y * draggable.scale
            draggable.scale *= zoomFactor
            refresh();
        }
        onPositionChanged: {
            if(mouse.modifiers == Qt.ShiftModifier) {
                _private.selectionEnabled = true;
                refresh();
                return;
            }
            _private.selectionEnabled = false;
            _private.selection = [];
            if(drag.active)
                refresh()
        }
        onPressed: {
            for(var i = 0; i<_private.selection.length; ++i)
                edgeRemoved(_private.selection[i])
        }

        // draw edges
        Canvas {
            id: canvas
            anchors.fill: parent
            onPaint: {
                if(!context)
                    getContext("2d");
                context.clearRect(0, 0, width, height);
                drawEdges(context);
                drawTmpEdge(context);
            }
        }

        // draw nodes
        Item {
            id: draggable
            transformOrigin: Item.TopLeft
            width: 1000
            height: 1000
            Repeater {
                id: repeater
                model: root.graph.nodes
                delegate: NodeDelegate {
                    width: 100
                    height: 80
                }
            }
        }
    }
}
