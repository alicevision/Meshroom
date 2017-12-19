import QtQuick 2.7
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

/**
  A component displaying a Graph (nodes, attributes and edges).
*/
Item {
    id: root

    property variant uigraph: null  /// Meshroom ui graph (UIGraph)
    readonly property variant graph: uigraph ? uigraph.graph : null  /// core graph contained in ui graph
    property variant nodeTypesModel: null  /// the list of node types that can be instantiated
    property bool readOnly: false
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

        onClicked: {
            if(mouse.button & Qt.RightButton)
            {
                // store mouse click position in 'draggable' coordinates as new node spawn position
                newNodeMenu.spawnPosition = mouseArea.mapToItem(draggable, mouse.x, mouse.y)
                newNodeMenu.popup()
            }
        }

        // Contextual Menu for creating new nodes
        // TODO: add filtering + validate on 'Enter'
        Menu {
            id: newNodeMenu
            property point spawnPosition

            function createNode(nodeType)
            {
                // add node via the proper command in uigraph
                uigraph.addNode(nodeType)
                // retrieve node delegate (the last one created in the node repeater)
                var item = nodeRepeater.itemAt(nodeRepeater.count-1)
                // convert mouse position
                // disable node animation on position
                item.animatePosition = false
                // set the node position
                item.x = spawnPosition.x
                item.y = spawnPosition.y
                // reactivate animation on position
                item.animatePosition = true
                // select this node
                draggable.selectNode(item)
            }

            onVisibleChanged: {
                if(visible) {
                    // when menu is shown,
                    // clear and give focus to the TextField filter
                    filterTextField.clear()
                    filterTextField.forceActiveFocus()
                }
            }

            TextField {
                id: filterTextField
                selectByMouse: true
                width: parent.width
                // ensure down arrow give focus to the first MenuItem
                // (without this, we have to pressed the down key twice to do so)
                Keys.onDownPressed: nextItemInFocusChain().forceActiveFocus()
            }

            Repeater {
                model: root.nodeTypesModel

                // Create Menu items from available node types model
                delegate: MenuItem {
                    id: menuItemDelegate
                    font.pointSize: 8
                    padding: 3
                    // Hide items that does not match the filter text
                    visible: modelData.toLowerCase().indexOf(filterTextField.text.toLocaleLowerCase()) > -1
                    text: modelData
                    Keys.onPressed: {
                        switch(event.key)
                        {
                        case Qt.Key_Return:
                        case Qt.Key_Enter:
                            // create node on validation (Enter/Return keys)
                            newNodeMenu.createNode(modelData)
                            newNodeMenu.dismiss()
                            break;
                        case Qt.Key_Home:
                            // give focus back to filter
                            filterTextField.forceActiveFocus()
                            break;
                        default:
                            break;
                        }
                    }
                    // Create node on mouse click
                    onClicked: newNodeMenu.createNode(modelData)

                    states: [
                        State {
                            // Additional property setting when the MenuItem is not visible
                            when: !visible
                            name: "invisible"
                            PropertyChanges {
                                target: menuItemDelegate
                                height: 0 // make sure the item is no visible by setting height to 0
                                focusPolicy: Qt.NoFocus // don't grab focus when not visible
                            }
                        }
                    ]
                }
            }
        }

        Item {
            id: draggable
            transformOrigin: Item.TopLeft
            width: 1000
            height: 1000

            function selectNode(delegate)
            {
                root.selectedNode = delegate.node
                delegate.forceActiveFocus()
            }

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
                    color: containsMouse && !readOnly ? palette.highlight : palette.text
                    opacity: 0.7
                    point1x: src.nodeItem.x + srcAnchor.x
                    point1y: src.nodeItem.y + srcAnchor.y
                    point2x: dst.nodeItem.x + dstAnchor.x
                    point2y: dst.nodeItem.y + dstAnchor.y
                    onPressed: {
                        if(!root.readOnly && event.button == Qt.RightButton)
                            uigraph.removeEdge(edge)
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
                    id: nodeDelegate

                    property bool animatePosition: true

                    node: object
                    width: root.nodeWidth
                    readOnly: root.readOnly
                    baseColor: root.selectedNode == node ? Qt.lighter("#607D8B", 1.2) : "#607D8B"

                    onAttributePinCreated: registerAttributePin(attribute, pin)

                    onPressed: draggable.selectNode(nodeDelegate)

                    Keys.onDeletePressed: uigraph.removeNode(node)

                    Behavior on x {
                        enabled: animatePosition
                        NumberAnimation {}
                    }
                    Behavior on y {
                        enabled: animatePosition
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
