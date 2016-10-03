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
        property variant edgeObj: null
    }

    // signals
    signal nodeMoved(var node)
    signal nodeLeftClicked(var node)
    signal nodeRightClicked(var node)
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
        _private.edgeObj = new Object();
        refresh();
    }
    function updateTmpEdge(node, plug, pos) {
        _private.edgeEnd = pos;
        _private.edgeObj.source = node.name;
        refresh();
    }
    function finalizeTmpEdge(node, plug, pos) {
        if(node && plug) {
            // add edge
            _private.edgeObj.plug = plug.key;
            _private.edgeObj.target = node.name;
            edgeAdded(_private.edgeObj);
        }
        // clear
        _private.edgeBegin = Qt.vector2d(0,0);
        _private.edgeEnd = Qt.vector2d(0,0);
        _private.edgeObj = null;
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
    function drawEdge(context, itemA, itemB, edgeObj) {
        if(!itemA || !itemB || !edgeObj)
            return;
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
            var index = _private.selection.indexOf(edgeObj);
            if(index<0)
                _private.selection.push(edgeObj);
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

    Flickable {
        anchors.fill: parent
        ScrollBar.vertical: ScrollBar {}
        ScrollBar.horizontal: ScrollBar {}
        clip: true
        contentWidth: canvas.width
        contentHeight: canvas.height
        // draw edges
        Canvas {
            id: canvas
            width: 1000
            height: 600
            onPaint: {
                if(!context)
                    getContext("2d");
                context.clearRect(0, 0, width, height);
                drawEdges(context);
                drawTmpEdge(context);
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
            onPressed: {
                for(var i = 0; i<_private.selection.length; ++i)
                    edgeRemoved(_private.selection[i])
            }
        }
    }

    // help msg
    Label {
        anchors.centerIn: parent
        visible: !root.graph.nodes || root.graph.nodes.count == 0
        text: "Add new nodes with [TAB]"
    }
}
