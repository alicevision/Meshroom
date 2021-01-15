import QtQuick 2.7
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import Controls 1.0
import Utils 1.0
import MaterialIcons 2.2

/**
  A component displaying a Graph (nodes, attributes and edges).
*/
Item {
    id: root

    property variant uigraph: null  /// Meshroom ui graph (UIGraph)
    readonly property variant graph: uigraph ? uigraph.graph : null  /// core graph contained in ui graph
    property variant nodeTypesModel: null  /// the list of node types that can be instantiated

    property var _attributeToDelegate: ({})

    // signals
    signal workspaceMoved()
    signal workspaceClicked()

    signal nodeDoubleClicked(var mouse, var node)
    signal computeRequest(var node)
    signal submitRequest(var node)

    // trigger initial fit() after initialization
    // (ensure GraphEditor has its final size)
    Component.onCompleted: firstFitTimer.start()

    Timer {
        id: firstFitTimer
        running: false
        interval: 10
        onTriggered: fit()
    }

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
        uigraph.selectedNode = node
    }

    /// Duplicate a node and optionnally all the following ones
    function duplicateNode(node, duplicateFollowingNodes) {
        var nodes = uigraph.duplicateNode(node, duplicateFollowingNodes)
        selectNode(nodes[0])
    }


    Keys.onPressed: {
        if(event.key === Qt.Key_F)
            fit()
        if(event.key === Qt.Key_Delete)
            if(event.modifiers == Qt.AltModifier)
                uigraph.removeNodesFrom(uigraph.selectedNode)
            else
                uigraph.removeNode(uigraph.selectedNode)
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
        cursorShape: drag.target == draggable ? Qt.ClosedHandCursor : Qt.ArrowCursor

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
            if (mouse.button != Qt.MiddleButton && mouse.modifiers == Qt.NoModifier) {
                selectNode(null)
                uigraph.clearNodesSelections()
            }
            if (mouse.button == Qt.LeftButton && (mouse.modifiers == Qt.NoModifier || mouse.modifiers == Qt.ControlModifier)) {
                boxSelect.startX = mouseX
                boxSelect.startY = mouseY
                boxSelectDraggable.x = mouseX
                boxSelectDraggable.y = mouseY
                drag.target = boxSelectDraggable
            }
            if (mouse.button == Qt.MiddleButton || (mouse.button == Qt.LeftButton && mouse.modifiers & Qt.ShiftModifier)) {
                drag.target = draggable // start drag
            }
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
            if(mouse.button == Qt.RightButton)
            {
                // store mouse click position in 'draggable' coordinates as new node spawn position
                newNodeMenu.spawnPosition = mouseArea.mapToItem(draggable, mouse.x, mouse.y);
                newNodeMenu.popup();
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
                    searchBar.clear()
                    searchBar.forceActiveFocus()
                }
            }

            SearchBar {
                id: searchBar
                width: parent.width
            }

            Repeater {
                model: root.nodeTypesModel

                // Create Menu items from available node types model
                delegate: MenuItem {
                    id: menuItemDelegate
                    font.pointSize: 8
                    padding: 3

                    // Hide items that does not match the filter text
                    visible: modelData.toLowerCase().indexOf(searchBar.text.toLowerCase()) > -1
                    // Reset menu currentIndex if highlighted items gets filtered out
                    onVisibleChanged: if(highlighted) newNodeMenu.currentIndex = 0
                    text: modelData
                    // Forward key events to the search bar to continue typing seamlessly
                    // even if this delegate took the activeFocus due to mouse hovering
                    Keys.forwardTo: [searchBar.textField]
                    Keys.onPressed: {
                        event.accepted = false;
                        switch(event.key)
                        {
                        case Qt.Key_Return:
                        case Qt.Key_Enter:
                            // create node on validation (Enter/Return keys)
                            newNodeMenu.createNode(modelData);
                            newNodeMenu.close();
                            event.accepted = true;
                            break;
                        default:
                            searchBar.textField.forceActiveFocus();
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

        // Informative contextual menu when graph is read-only
        Menu {
            id: lockedMenu
            MenuItem {
                id: item
                font.pointSize: 8
                enabled: false
                text: "Computing - Graph is Locked!"
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
                    enabled: edgeMenu.currentEdge && !edgeMenu.currentEdge.dst.node.locked
                    text: "Remove"
                    onTriggered: uigraph.removeEdge(edgeMenu.currentEdge)
                }
            }

            // Edges
            Repeater {
                id: edgesRepeater

                // delay edges loading after nodes (edges needs attribute pins to be created)
                model: nodeRepeater.loaded && root.graph ? root.graph.edges : undefined

                delegate: Edge {
                    property var src: root._attributeToDelegate[edge.src]
                    property var dst: root._attributeToDelegate[edge.dst]
                    property bool isValidEdge: src != undefined && dst != undefined
                    visible: isValidEdge

                    property bool inFocus: containsMouse || (edgeMenu.opened && edgeMenu.currentEdge == edge)

                    edge: object
                    color: inFocus ? activePalette.highlight : activePalette.text
                    thickness: inFocus ? 2 : 1
                    opacity: 0.7
                    point1x: isValidEdge ? src.globalX + src.outputAnchorPos.x : 0
                    point1y: isValidEdge ? src.globalY + src.outputAnchorPos.y : 0
                    point2x: isValidEdge ? dst.globalX + dst.inputAnchorPos.x : 0
                    point2y: isValidEdge ? dst.globalY + dst.inputAnchorPos.y : 0
                    onPressed: {
                        const canEdit = !edge.dst.node.locked

                        if(event.button == Qt.RightButton)
                        {
                            if(canEdit && (event.modifiers & Qt.AltModifier)) {
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
                //canSubmitOrCompute: return int n : 0 >= n <= 3 | n=0 cannot submit or compute | n=1 can compute | n=2 can submit | n=3 can compute & submit
                property int canSubmitOrCompute: currentNode != null && uigraph.graph.canSubmitOrCompute(currentNode)
                onClosed: currentNode = null

                MenuItem {
                    text: "Compute"
                    enabled: nodeMenu.canComputeNode && (nodeMenu.canSubmitOrCompute%2 == 1) //canSubmit if canSubmitOrCompute == 1(can compute) or 3(can compute & submit)
                    onTriggered: {
                        computeRequest(nodeMenu.currentNode)
                    }
                }
                MenuItem {
                    text: "Submit"
                    enabled: nodeMenu.canComputeNode && nodeMenu.canSubmitOrCompute > 1
                    visible: uigraph.canSubmit
                    height: visible ? implicitHeight : 0
                    onTriggered: submitRequest(nodeMenu.currentNode)
                }
                MenuItem {
                    text: "Stop Computation"
                    enabled: nodeMenu.currentNode ? nodeMenu.currentNode.canBeStopped() : false
                    visible: enabled
                    height: visible ? implicitHeight : 0
                    onTriggered: uigraph.stopNodeComputation(nodeMenu.currentNode)
                }
                MenuItem {
                    text: "Cancel Computation"
                    enabled: nodeMenu.currentNode ? nodeMenu.currentNode.canBeCanceled() : false
                    visible: enabled
                    height: visible ? implicitHeight : 0
                    onTriggered: uigraph.cancelNodeComputation(nodeMenu.currentNode)
                }
                MenuItem {
                    text: "Open Folder"
                    onTriggered: Qt.openUrlExternally(Filepath.stringToUrl(nodeMenu.currentNode.internalFolder))
                }
                MenuSeparator {}
                MenuItem {
                    text: "Duplicate Node" + (duplicateFollowingButton.hovered ? "s From Here" : uigraph.nodeSelection(nodeMenu.currentNode) ? "s" : "")
                    enabled: true
                    onTriggered: duplicateNode(nodeMenu.currentNode, false)
                    MaterialToolButton {
                        id: duplicateFollowingButton
                        height: parent.height
                        anchors { right: parent.right; rightMargin: parent.padding }
                        text: MaterialIcons.fast_forward
                        onClicked: {
                            duplicateNode(nodeMenu.currentNode, true);
                            nodeMenu.close();
                        }
                    }
                }
                MenuItem {
                    text: "Remove Node" + (removeFollowingButton.hovered ? "s From Here" : uigraph.nodeSelection(nodeMenu.currentNode) ? "s" : "")
                    enabled: nodeMenu.currentNode ? !nodeMenu.currentNode.locked : false
                    onTriggered: uigraph.removeNode(nodeMenu.currentNode)
                    MaterialToolButton {
                        id: removeFollowingButton
                        height: parent.height
                        anchors { right: parent.right; rightMargin: parent.padding }
                        text: MaterialIcons.fast_forward
                        onClicked: {
                            uigraph.removeNodesFrom(nodeMenu.currentNode);
                            nodeMenu.close();
                        }
                    }
                }
                MenuSeparator {}
                MenuItem {
                    text: "Delete Data" + (deleteFollowingButton.hovered ? " From Here" : "" ) + "..."
                    enabled: {
                        if(!nodeMenu.currentNode)
                            return false
                        // Check if the current node is locked (needed because it does not belong to its own duplicates list)
                        if(nodeMenu.currentNode.locked)
                            return false
                        // Check if at least one of the duplicate nodes is locked
                        for(let i = 0; i < nodeMenu.currentNode.duplicates.count; ++i) {
                            if(nodeMenu.currentNode.duplicates.at(i).locked)
                                return false
                        }
                        return true
                    }

                    function showConfirmationDialog(deleteFollowing) {
                        var obj = deleteDataDialog.createObject(root,
                                           {
                                               "node": nodeMenu.currentNode,
                                               "deleteFollowing": deleteFollowing
                                           });
                        obj.open()
                        nodeMenu.close();
                    }

                    onTriggered: showConfirmationDialog(false)

                    MaterialToolButton {
                        id: deleteFollowingButton
                        anchors { right: parent.right; rightMargin: parent.padding }
                        height: parent.height
                        text: MaterialIcons.fast_forward
                        onClicked: parent.showConfirmationDialog(true)
                    }

                    // Confirmation dialog for node cache deletion
                    Component {
                        id: deleteDataDialog
                        MessageDialog  {
                            property var node
                            property bool deleteFollowing: false

                            focus: true
                            modal: false
                            header.visible: false

                            text: "Delete Data of '" + node.label + (deleteFollowing ?  "' and following Nodes?" : "'?")
                            helperText: "Warning: This operation can not be undone."
                            standardButtons: Dialog.Yes | Dialog.Cancel

                            onAccepted: {
                                if(deleteFollowing)
                                    graph.clearDataFrom(node);
                                else
                                    uigraph.clearData(node);
                            }
                            onClosed: destroy()
                        }
                    }
                }
            }

            // Nodes
            Repeater {
                id: nodeRepeater

                model: root.graph ? root.graph.nodes : undefined
                property bool loaded: model ? count === model.count : false
                property bool dragging: false

                delegate: Node {
                    id: nodeDelegate

                    node: object
                    width: uigraph.layout.nodeWidth

                    mainSelected: uigraph.selectedNode === node
                    selected: uigraph.selectedNodes.contains(node)
                    hovered: uigraph.hoveredNode === node

                    onAttributePinCreated: registerAttributePin(attribute, pin)
                    onAttributePinDeleted: unregisterAttributePin(attribute, pin)

                    onPressed: {
                        if (mouse.button == Qt.LeftButton) {
                            if (mouse.modifiers & Qt.ControlModifier) {
                                if (mainSelected) {
                                    // left clicking a selected node twice with control will deselect it
                                    uigraph.selectedNodes.remove(node)
                                    uigraph.selectedNodesChanged()
                                    selectNode(null)
                                    return
                                } else if (!selected) {
                                    uigraph.selectedNodes.append(node)
                                    uigraph.selectedNodesChanged()
                                }
                            } else if (mouse.modifiers & Qt.AltModifier) {
                                duplicateNode(node, true)
                            } else if (!mainSelected && !selected) {
                                uigraph.clearNodesSelections()
                            }
                        } else if (mouse.button == Qt.RightButton) {
                            if (!mainSelected && !selected) {
                                uigraph.clearNodesSelections()
                            }
                            nodeMenu.currentNode = node
                            nodeMenu.popup()
                        }
                        selectNode(node)
                    }

                    onDoubleClicked: root.nodeDoubleClicked(mouse, node)

                    onMoved: uigraph.moveNode(node, position)

                    onEntered: uigraph.hoveredNode = node
                    onExited: uigraph.hoveredNode = null

                    onPositionChanged: {
                        if (dragging && uigraph.selectedNodes.contains(node)) {
                            // update all selected nodes positions with this node that is being dragged
                            for (var i = 0; i < nodeRepeater.count; i++) {
                                var otherNode = nodeRepeater.itemAt(i)
                                if (uigraph.selectedNodes.contains(otherNode.node) && otherNode.node != node) {
                                    otherNode.x = otherNode.node.x + (x - node.x)
                                    otherNode.y = otherNode.node.y + (y - node.y)
                                }
                            }
                        }
                    }

                    // allow all nodes to know if they are being dragged
                    onDraggingChanged: nodeRepeater.dragging = dragging

                    // must not be enabled during drag because the other nodes will be slow to match the movement of the node being dragged
                    Behavior on x {
                        enabled: !nodeRepeater.dragging
                        NumberAnimation { duration: 100 }
                    }
                    Behavior on y {
                        enabled: !nodeRepeater.dragging
                        NumberAnimation { duration: 100 }
                    }
                }
            }
        }

        Rectangle {
            id: boxSelect
            property int startX: 0
            property int startY: 0
            property int toX: boxSelectDraggable.x - startX
            property int toY: boxSelectDraggable.y - startY

            x: toX < 0 ? startX + toX : startX
            y: toY < 0 ? startY + toY : startY
            width: Math.abs(toX)
            height: Math.abs(toY)

            color: "transparent"
            border.color: activePalette.text
            visible: mouseArea.drag.target == boxSelectDraggable

            onVisibleChanged: {
                if (!visible) {
                    uigraph.boxSelect(boxSelect, draggable)
                }
            }
        }

        Item {
            id: boxSelectDraggable
        }
    }

    // Toolbar
    FloatingPane {
        padding: 2
        anchors.bottom: parent.bottom
        RowLayout {
            spacing: 4
            // Fit
            MaterialToolButton {
                text: MaterialIcons.fullscreen
                ToolTip.text: "Fit"
                onClicked: root.fit()
            }
            // Auto-Layout
            MaterialToolButton {
                text: MaterialIcons.linear_scale
                ToolTip.text: "Auto-Layout"
                onClicked: uigraph.layout.reset()
            }

            // Separator
            Rectangle {
                Layout.fillHeight: true
                Layout.margins: 2
                implicitWidth: 1
                color: activePalette.window
            }
            // Settings
            MaterialToolButton {
                text: MaterialIcons.settings
                font.pointSize: 11
                onClicked: menu.open()
                Menu {
                    id: menu
                    y: -height
                    padding: 4
                    RowLayout {
                        spacing: 2
                        Label {
                            padding: 2
                            text: "Auto-Layout Depth:"
                        }
                        ComboBox {
                            flat: true
                            model: ['Minimum', 'Maximum']
                            implicitWidth: 80
                            currentIndex: uigraph.layout.depthMode
                            onActivated: {
                                uigraph.layout.depthMode = currentIndex
                            }
                        }
                    }
                }
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
        var bbox = Qt.rect(first.x, first.y, first.x + first.width, first.y + first.height)
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
