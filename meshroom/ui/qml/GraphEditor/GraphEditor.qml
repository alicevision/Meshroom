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

    property var _attributeToDelegate: ({})

    // signals
    signal workspaceMoved()
    signal workspaceClicked()
    signal nodeDoubleClicked(var node)


    clip: true

    SystemPalette { id: activePalette }

    /// Get node delegate for the given node object
    function nodeDelegate(node)
    {
        for(var i=0; i<nodeRepeater.count; ++i)
        {
            if(nodeRepeater.itemAt(i).node === node)
                return nodeRepeater.itemAt(i)
        }
        return undefined
    }

    /// Select node delegate
    function selectNode(node)
    {
        root.selectedNode = node
    }

    /// Duplicate a node and optionnally all the following ones
    function duplicateNode(node, duplicateFollowingNodes) {
        var nodes = uigraph.duplicateNode(node, duplicateFollowingNodes)
        selectNode(nodes[0])
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        property double factor: 1.15
        property real minZoom: 0.1
        property real maxZoom: 2.0
        // Activate multisampling for edges antialiasing
        layer.enabled: true
        layer.samples: 8

        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
        drag.threshold: 0
        onWheel: {
            var zoomFactor = wheel.angleDelta.y > 0 ? factor : 1/factor
            var scale = draggable.scale * zoomFactor
            scale = Math.min(Math.max(minZoom, scale), maxZoom)
            if(draggable.scale == scale)
                return
            var point = mapToItem(draggable, wheel.x, wheel.y)
            draggable.x += (1-zoomFactor) * point.x * draggable.scale
            draggable.y += (1-zoomFactor) * point.y * draggable.scale
            draggable.scale = scale
            workspaceMoved()
        }

        onPressed: {
            if(mouse.button & Qt.MiddleButton || (mouse.button & Qt.LeftButton && mouse.modifiers & Qt.ControlModifier))
                drag.target = draggable // start drag
        }
        onReleased: {
            drag.target = undefined // stop drag
            root.forceActiveFocus()
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
                var node = uigraph.addNewNode(nodeType, spawnPosition)
                selectNode(node)
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

            Menu {
                id: edgeMenu
                property var currentEdge: null
                MenuItem {
                    text: "Remove"
                    enabled: !root.readOnly
                    onTriggered: uigraph.removeEdge(edgeMenu.currentEdge)
                }
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

                    property bool inFocus: containsMouse || (edgeMenu.opened && edgeMenu.currentEdge == edge)

                    edge: object
                    color: inFocus ? activePalette.highlight : activePalette.text
                    thickness: inFocus ? 2 : 1
                    opacity: 0.7
                    point1x: src.nodeItem.x + srcAnchor.x
                    point1y: src.nodeItem.y + srcAnchor.y
                    point2x: dst.nodeItem.x + dstAnchor.x
                    point2y: dst.nodeItem.y + dstAnchor.y
                    onPressed: {
                        if(event.button == Qt.RightButton)
                        {
                            if(!root.readOnly && event.modifiers & Qt.AltModifier) {
                                uigraph.removeEdge(edge)
                            }
                            else {
                                edgeMenu.currentEdge = edge
                                edgeMenu.popup()
                            }
                        }
                    }
                }
            }

            Menu {
                id: nodeMenu
                property var currentNode: null
                property bool canComputeNode: currentNode != null && uigraph.graph.canCompute(currentNode)
                onClosed: currentNode = null

                MenuItem {
                    text: "Compute"
                    enabled: !root.readOnly && nodeMenu.canComputeNode
                    onTriggered: uigraph.execute(nodeMenu.currentNode)
                }
                MenuItem {
                    text: "Submit"
                    enabled: !root.readOnly && nodeMenu.canComputeNode
                    onTriggered: uigraph.submit(nodeMenu.currentNode)
                }
                MenuItem {
                    text: "Open Folder"
                    onTriggered: Qt.openUrlExternally(Filepath.stringToUrl(nodeMenu.currentNode.internalFolder))
                }
                MenuSeparator {}
                MenuItem {
                    text: "Duplicate"
                    onTriggered: duplicateNode(nodeMenu.currentNode, false)
                }
                MenuItem {
                    text: "Duplicate From Here"
                    onTriggered: duplicateNode(nodeMenu.currentNode, true)
                }
                MenuSeparator {}
                MenuItem {
                    text: "Clear Data"
                    enabled: !root.readOnly
                    onTriggered: nodeMenu.currentNode.clearData()
                }
                MenuItem {
                    text: "Delete Node"
                    enabled: !root.readOnly
                    onTriggered: uigraph.removeNode(nodeMenu.currentNode)
                }
            }

            // Nodes
            Repeater {
                id: nodeRepeater

                model: root.graph.nodes
                property bool loaded: count === model.count

                delegate: Node {
                    id: nodeDelegate

                    property bool animatePosition: true

                    node: object
                    width: uigraph.layout.nodeWidth
                    readOnly: root.readOnly
                    selected: root.selectedNode == node
                    onSelectedChanged: if(selected) forceActiveFocus()

                    onAttributePinCreated: registerAttributePin(attribute, pin)
                    onAttributePinDeleted: unregisterAttributePin(attribute, pin)

                    onPressed: {
                        if(mouse.modifiers & Qt.AltModifier)
                        {
                            duplicateNode(node, true)
                        }
                        else
                        {
                            selectNode(node)
                        }
                        if(mouse.button == Qt.RightButton)
                        {
                            nodeMenu.currentNode = node
                            nodeMenu.popup()
                        }
                    }

                    onDoubleClicked: root.nodeDoubleClicked(node)

                    onMoved: uigraph.moveNode(node, position)

                    Keys.onDeletePressed: uigraph.removeNode(node)

                    Behavior on x {
                        enabled: animatePosition
                        NumberAnimation { duration: 100 }
                    }
                    Behavior on y {
                        enabled: animatePosition
                        NumberAnimation { duration: 100 }
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
            onClicked: uigraph.layout.reset()
            z: 10
        }
        ComboBox {
            model: ['Min Depth', 'Max Depth']
            currentIndex: uigraph.layout.depthMode
            onActivated: {
                uigraph.layout.depthMode = currentIndex
            }
        }
    }

    function registerAttributePin(attribute, pin)
    {
        root._attributeToDelegate[attribute] = pin
    }
    function unregisterAttributePin(attribute, pin)
    {
        delete root._attributeToDelegate[attribute]
    }

    function boundingBox()
    {
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
        return bbox;
    }

    // Fit graph to fill root
    function fit() {
        // compute bounding box
        var bbox = boundingBox()
        // rescale
        draggable.scale = Math.min(root.width/bbox.width, root.height/bbox.height)
        // recenter
        draggable.x = bbox.x*draggable.scale*-1 + (root.width-bbox.width*draggable.scale)*0.5
        draggable.y = bbox.y*draggable.scale*-1 + (root.height-bbox.height*draggable.scale)*0.5
    }

}
