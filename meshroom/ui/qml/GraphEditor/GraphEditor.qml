import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Controls 1.0
import MaterialIcons 2.2
import Utils 1.0

/**
 * A component displaying a Graph (nodes, attributes and edges).
 */

Item {
    id: root

    property variant uigraph: null  /// Meshroom UI graph (UIGraph)
    readonly property variant graph: uigraph ? uigraph.graph : null  /// Core graph contained in the UI graph
    property variant nodeTypesModel: null  /// The list of node types that can be instantiated
    property real maxZoom: 2.0
    property real minZoom: 0.1

    property var edgeAboutToBeRemoved: undefined

    property var _attributeToDelegate: ({})

    // Signals
    signal workspaceMoved()
    signal workspaceClicked()

    signal nodeDoubleClicked(var mouse, var node)
    signal computeRequest(var nodes)
    signal submitRequest(var nodes)

    signal dataDeleted()

    property int nbMeshroomScenes: 0
    property int nbDraggedFiles: 0
    signal filesDropped(var drop, var mousePosition)  // Files have been dropped

    // Trigger initial fit() after initialization
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
    function nodeDelegate(node) {
        for(var i = 0; i < nodeRepeater.count; ++i) {
            if (nodeRepeater.itemAt(i).node === node)
                return nodeRepeater.itemAt(i)
        }
        return undefined
    }

    /// Select node delegate
    function selectNode(node) {
        uigraph.selectedNode = node
        if (node !== null) {
            uigraph.appendSelection(node)
            uigraph.selectedNodesChanged()
        }
    }

    onDataDeleted: {
        if (computeMenuItem.recompute) {
            computeRequest(uigraph.selectedNodes)
            computeMenuItem.recompute = false
        } 
        else if (submitMenuItem.resubmit) {
            submitRequest(uigraph.selectedNodes)
            submitMenuItem.resubmit = false
        }
    }

    /// Duplicate a node and optionally all the following ones
    function duplicateNode(duplicateFollowingNodes) {
        var nodes
        if (duplicateFollowingNodes) {
            nodes = uigraph.duplicateNodesFrom(uigraph.selectedNodes)
        } else {
            nodes = uigraph.duplicateNodes(uigraph.selectedNodes)
        }
        uigraph.clearNodeSelection()
        uigraph.selectedNode = nodes[0]
        uigraph.selectNodes(nodes)
    }

    /// Copy node content to clipboard
    function copyNodes() {
        var nodeContent = uigraph.getSelectedNodesContent()
        if (nodeContent !== '') {
            Clipboard.clear()
            Clipboard.setText(nodeContent)
        }
    }

    /// Paste content of clipboard to graph editor and create new node if valid
    function pasteNodes() {
        var finalPosition = undefined
        var centerPosition = false
        if (mouseArea.containsMouse) {
            if (uigraph.hoveredNode !== null) {
                var node = nodeDelegate(uigraph.hoveredNode)
                finalPosition = Qt.point(node.mousePosition.x + node.x, node.mousePosition.y + node.y)
            } else {
                finalPosition = mapToItem(draggable, mouseArea.mouseX, mouseArea.mouseY)
            }
        } else {
            finalPosition = getCenterPosition()
            centerPosition = true
        }

        var copiedContent = Clipboard.getText()
        var nodes = uigraph.pasteNodes(copiedContent, finalPosition, centerPosition)
        if (nodes.length > 0) {
            uigraph.clearNodeSelection()
            uigraph.selectedNode = nodes[0]
            uigraph.selectNodes(nodes)
        }
    }

    /// Get the coordinates of the point at the center of the GraphEditor
    function getCenterPosition() {
        return mapToItem(draggable, mouseArea.width / 2, mouseArea.height / 2)
    }

    Keys.onPressed: function(event) {
        if (event.key === Qt.Key_F) {
            fit()
        } else if (event.key === Qt.Key_Delete) {
            if (event.modifiers === Qt.AltModifier) {
                uigraph.removeNodesFrom(uigraph.selectedNodes)
            } else {
                uigraph.removeNodes(uigraph.selectedNodes)
            }
        } else if (event.key === Qt.Key_D) {
            duplicateNode(event.modifiers === Qt.AltModifier)
        } else if (event.key === Qt.Key_X && event.modifiers === Qt.ControlModifier) {
            copyNodes()
            uigraph.removeNodes(uigraph.selectedNodes)
        } else if (event.key === Qt.Key_C && event.modifiers === Qt.ControlModifier) {
            copyNodes()
        } else if (event.key === Qt.Key_V && event.modifiers === Qt.ControlModifier) {
            pasteNodes()
        } else if (event.key === Qt.Key_Tab) {
            event.accepted = true
            if (mouseArea.containsMouse) {
                newNodeMenu.spawnPosition = mouseArea.mapToItem(draggable, mouseArea.mouseX, mouseArea.mouseY)
                newNodeMenu.popup()
            }
        }
    }

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
        cursorShape: drag.target == draggable ? Qt.ClosedHandCursor : Qt.ArrowCursor

        onWheel: function(wheel) {
            var zoomFactor = wheel.angleDelta.y > 0 ? factor : 1 / factor
            var scale = draggable.scale * zoomFactor
            scale = Math.min(Math.max(minZoom, scale), maxZoom)
            if (draggable.scale == scale)
                return
            var point = mapToItem(draggable, wheel.x, wheel.y)
            draggable.x += (1 - zoomFactor) * point.x * draggable.scale
            draggable.y += (1 - zoomFactor) * point.y * draggable.scale
            draggable.scale = scale
            workspaceMoved()
        }

        onPressed: function(mouse) {
            if (mouse.button != Qt.MiddleButton && mouse.modifiers == Qt.NoModifier) {
                uigraph.clearNodeSelection()
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
            if (drag.active)
                workspaceMoved()
        }

        onClicked: function(mouse) {
            if (mouse.button == Qt.RightButton) {
                // Store mouse click position in 'draggable' coordinates as new node spawn position
                newNodeMenu.spawnPosition = mouseArea.mapToItem(draggable, mouse.x, mouse.y)
                newNodeMenu.popup()
            }
        }

        // Contextual Menu for creating new nodes
        // TODO: add filtering + validate on 'Enter'
        Menu {
            id: newNodeMenu
            property point spawnPosition
            property variant menuKeys: Object.keys(root.nodeTypesModel).concat(Object.values(MeshroomApp.pipelineTemplateNames))
            height: searchBar.height + nodeMenuRepeater.height + instantiator.height

            function createNode(nodeType) {
                uigraph.clearNodeSelection() // Ensures that only the created node / imported pipeline will be selected

                // "nodeType" might be a pipeline (artificially added in the "Pipelines" category) instead of a node
                // If it is not a pipeline to import, then it must be a node
                if (!importPipeline(nodeType)) {
                    // Add node via the proper command in uigraph
                    var node = uigraph.addNewNode(nodeType, spawnPosition)
                    selectNode(node)
                }
                close()
            }

            function importPipeline(pipeline) {
                if (MeshroomApp.pipelineTemplateNames.includes(pipeline)) {
                    var url = MeshroomApp.pipelineTemplateFiles[MeshroomApp.pipelineTemplateNames.indexOf(pipeline)]["path"]
                    var nodes = uigraph.importProject(Filepath.stringToUrl(url), spawnPosition)
                    uigraph.selectedNode = nodes[0]
                    uigraph.selectNodes(nodes)
                    return true
                }
                return false
            }

            function parseCategories() {
                // Organize nodes based on their category
                // {"category1": ["node1", "node2"], "category2": ["node3", "node4"]}
                let categories = {};
                for (const [name, data] of Object.entries(root.nodeTypesModel)) {
                    let category = data["category"];
                    if (categories[category] === undefined) {
                        categories[category] = []
                    }
                    categories[category].push(name)
                }

                // Add a "Pipelines" category, filled with the list of templates to create pipelines from the menu
                categories["Pipelines"] = MeshroomApp.pipelineTemplateNames

                return categories
            }

            onVisibleChanged: {
                searchBar.clear()
                if (visible) {
                    // When menu is shown, give focus to the TextField filter
                    searchBar.forceActiveFocus()
                }
            }

            SearchBar {
                id: searchBar
                width: parent.width
            }

            // menuItemDelegate is wrapped in a component so it can be used in both the search bar and sub-menus
            Component {
                id: menuItemDelegateComponent
                MenuItem {
                    id: menuItemDelegate
                    font.pointSize: 8
                    padding: 3

                    // Hide items that does not match the filter text
                    visible: modelData.toLowerCase().indexOf(searchBar.text.toLowerCase()) > -1
                    text: modelData
                    // Forward key events to the search bar to continue typing seamlessly
                    // even if this delegate took the activeFocus due to mouse hovering
                    Keys.forwardTo: [searchBar.textField]
                    Keys.onPressed: function(event) {
                        event.accepted = false;
                        switch (event.key) {
                            case Qt.Key_Return:
                            case Qt.Key_Enter:
                                // Create node on validation (Enter/Return keys)
                                newNodeMenu.createNode(modelData)
                                event.accepted = true
                                break
                            case Qt.Key_Up:
                            case Qt.Key_Down:
                            case Qt.Key_Left:
                            case Qt.Key_Right:
                                break  // Ignore if arrow key was pressed to let the menu be controlled
                            default:
                                searchBar.forceActiveFocus()
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
                                height: 0  // Make sure the item is no visible by setting height to 0
                                focusPolicy: Qt.NoFocus  // Don't grab focus when not visible
                            }
                        }
                    ]
                }
            }

            Repeater {
                id: nodeMenuRepeater
                model: searchBar.text !== "" ? Object.values(newNodeMenu.menuKeys) : undefined

                // Create Menu items from available items
                delegate: menuItemDelegateComponent
            }

            // Dynamically add the menu categories
            Instantiator {
                id: instantiator
                model: (searchBar.text === "") ? Object.keys(newNodeMenu.parseCategories()).sort() : undefined
                onObjectAdded: function(index, object) {
                    // Add sub-menu under the search bar
                    newNodeMenu.insertMenu(index + 1, object)
                }
                onObjectRemoved: function(index, object) {
                    newNodeMenu.removeMenu(object)
                }

                delegate: Menu {
                    title: modelData
                    id: newNodeSubMenu

                    Instantiator {
                        model: newNodeMenu.visible ? newNodeMenu.parseCategories()[modelData] : undefined
                        onObjectAdded: function(index, object) {
                            newNodeSubMenu.insertItem(index, object)
                        }
                        onObjectRemoved: function(index, object) {
                            newNodeSubMenu.removeItem(object)
                        }
                        delegate: menuItemDelegateComponent
                    }
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

            Popup {
                id: edgeMenu
                property var currentEdge: null
                property bool forLoop: false

                onOpened: {
                    expandButton.canExpand = uigraph.canExpandForLoop(edgeMenu.currentEdge)
                }

                contentItem: Row {
                    IntSelector {
                        id: loopIterationSelector
                        tooltipText: "Iterations"
                        visible: edgeMenu.currentEdge && edgeMenu.forLoop

                        enabled: expandButton.canExpand

                        property var listAttr: edgeMenu.currentEdge ? edgeMenu.currentEdge.src.root : null

                        Connections {
                            target: edgeMenu
                            function onCurrentEdgeChanged() {
                                if (edgeMenu.currentEdge) {
                                    loopIterationSelector.listAttr = edgeMenu.currentEdge.src.root
                                    loopIterationSelector.value = loopIterationSelector.listAttr ? loopIterationSelector.listAttr.value.indexOf(edgeMenu.currentEdge.src) + 1 : 0
                                }
                            }
                        }

                        // We add 1 to the index because of human readable index (starting at 1) 
                        value: listAttr ? listAttr.value.indexOf(edgeMenu.currentEdge.src) + 1 : 0
                        range: { "min": 1, "max": listAttr ? listAttr.value.count : 0 }

                        onValueChanged: {
                            if (listAttr === null) {
                                return
                            }
                            const newSrcAttr = listAttr.value.at(value - 1)
                            const dst = edgeMenu.currentEdge.dst

                            // If the edge exists, do not replace it
                            if (newSrcAttr === edgeMenu.currentEdge.src && dst === edgeMenu.currentEdge.dst) {
                                return
                            }
                            edgeMenu.currentEdge = uigraph.replaceEdge(edgeMenu.currentEdge, newSrcAttr, dst)
                        }
                    }

                    MaterialToolButton {
                        font.pointSize: 13
                        ToolTip.text: "Remove Edge"
                        enabled: edgeMenu.currentEdge && !edgeMenu.currentEdge.dst.node.locked && !edgeMenu.currentEdge.dst.isReadOnly
                        text: MaterialIcons.delete_
                        onClicked: {
                            uigraph.removeEdge(edgeMenu.currentEdge)
                            edgeMenu.close()
                        }
                    }

                    MaterialToolButton {
                        id: expandButton

                        property bool canExpand: edgeMenu.currentEdge && edgeMenu.forLoop

                        visible: edgeMenu.currentEdge && edgeMenu.forLoop && canExpand
                        enabled: edgeMenu.currentEdge && !edgeMenu.currentEdge.dst.node.locked && !edgeMenu.currentEdge.dst.isReadOnly
                        font.pointSize: 13
                        ToolTip.text: "Expand"
                        text: MaterialIcons.open_in_full

                        onClicked: {
                            edgeMenu.currentEdge = uigraph.expandForLoop(edgeMenu.currentEdge)
                            canExpand = false
                            edgeMenu.close()
                        }
                    }

                    MaterialToolButton {
                        id: collapseButton

                        visible: edgeMenu.currentEdge && edgeMenu.forLoop && !expandButton.canExpand
                        enabled: edgeMenu.currentEdge && !edgeMenu.currentEdge.dst.node.locked && !edgeMenu.currentEdge.dst.isReadOnly
                        font.pointSize: 13
                        ToolTip.text: "Collapse"
                        text: MaterialIcons.close_fullscreen

                        onClicked: {
                            uigraph.collapseForLoop(edgeMenu.currentEdge)
                            expandButton.canExpand = true
                            edgeMenu.close()
                        }
                    }
                }
            }

            // Edges
            Repeater {
                id: edgesRepeater

                // Delay edges loading after nodes (edges needs attribute pins to be created)
                model: nodeRepeater.loaded && root.graph ? root.graph.edges : undefined

                delegate: Edge {
                    property var src: root._attributeToDelegate[edge.src]
                    property var dst: root._attributeToDelegate[edge.dst]
                    property bool isValidEdge: src !== undefined && dst !== undefined
                    visible: isValidEdge && src.visible && dst.visible

                    property bool forLoop: src.attribute.type === "ListAttribute" && dst.attribute.type != "ListAttribute"

                    property bool inFocus: containsMouse || (edgeMenu.opened && edgeMenu.currentEdge === edge)

                    edge: object
                    isForLoop: forLoop
                    loopSize: forLoop ? edge.src.root.value.count : 0
                    iteration: forLoop ? edge.src.root.value.indexOf(edge.src) : 0
                    color: edge.dst === root.edgeAboutToBeRemoved ? "red" : inFocus ? activePalette.highlight : activePalette.text
                    thickness: {
                        if (forLoop) {
                            return (inFocus) ? 4 : 3
                        }
                        return (inFocus) ? 2 : 1
                    }
                    point1x: isValidEdge ? src.globalX + src.outputAnchorPos.x : 0
                    point1y: isValidEdge ? src.globalY + src.outputAnchorPos.y : 0
                    point2x: isValidEdge ? dst.globalX + dst.inputAnchorPos.x : 0
                    point2y: isValidEdge ? dst.globalY + dst.inputAnchorPos.y : 0
                    onPressed: function(event) {
                        const canEdit = !edge.dst.node.locked

                        if (event.button) {
                            if (canEdit && (event.modifiers & Qt.AltModifier)) {
                                uigraph.removeEdge(edge)
                            } else {
                                edgeMenu.currentEdge = edge
                                edgeMenu.forLoop = forLoop
                                var spawnPosition = mouseArea.mapToItem(draggable, mouseArea.mouseX, mouseArea.mouseY)
                                edgeMenu.x = spawnPosition.x
                                edgeMenu.y = spawnPosition.y
                                edgeMenu.open()
                            }
                        }
                    }

                    Component.onDestruction: {
                        // Handles the case where the edge is destroyed while hidden because it is replaced: the pins should be re-enabled
                        if (!_window.isClosing) {
                            // When the window is closing, the QML context becomes invalid, which causes function calls to result in errors
                            if (src && src !== undefined)
                                src.updatePin(true, true)  // isSrc = true, isVisible = true
                            if (dst && dst !== undefined)
                                dst.updatePin(false, true)  // isSrc = false, isVisible = true
                        }
                    }

                }
            }

            Menu {
                id: nodeMenu
                property var currentNode: null
                property bool canComputeNode: currentNode != null && uigraph.graph.canComputeTopologically(currentNode)
                // canSubmitOrCompute: return int n : 0 >= n <= 3 | n=0 cannot submit or compute | n=1 can compute | n=2 can submit | n=3 can compute & submit
                property int canSubmitOrCompute: currentNode != null && uigraph.graph.canSubmitOrCompute(currentNode)
                property bool isComputed: {
                    var count = 0
                    for (var i = 0; i < uigraph.selectedNodes.count; ++i) {
                        var node = uigraph.selectedNodes.at(i)
                        if (!node)
                            continue
                        if (!node.isComputed)
                            return false
                        count += 1
                    }
                    return count > 0
                }
                width: 220
                onClosed: currentNode = null

                MenuItem {
                    id: computeMenuItem
                    property bool recompute: false
                    text: nodeMenu.isComputed ? "Recompute" : "Compute"
                    visible: {
                        var count = 0
                        for (var i = 0; i < uigraph.selectedNodes.count; ++i) {
                            var node = uigraph.selectedNodes.at(i)
                            if (!node)
                                continue
                            if (!node.isComputable)
                                return false
                            count += 1
                        }
                        return count > 0
                    }
                    height: visible ? implicitHeight : 0

                    enabled: {
                        var canCompute = false
                        for (var i = 0; i < uigraph.selectedNodes.count; ++i) {
                            var node = uigraph.selectedNodes.at(i)
                            if (!node)
                                continue
                            if (uigraph.graph.canComputeTopologically(node)) {
                                if (nodeMenu.isComputed) {
                                    canCompute = true
                                } else if (uigraph.graph.canSubmitOrCompute(node) % 2 == 1) {
                                    canCompute = true
                                }
                            }
                        }
                        return canCompute  // canSubmit if canSubmitOrCompute == 1(can compute) or 3(can compute & submit)
                    }

                    onTriggered: {
                        if (nodeMenu.isComputed) {
                            recompute = true
                            deleteDataMenuItem.showConfirmationDialog(false)
                        } else {
                            computeRequest(uigraph.selectedNodes)
                        }
                    }
                }
                MenuItem {
                    id: submitMenuItem
                    property bool resubmit: false
                    text: nodeMenu.isComputed ? "Re-Submit" : "Submit"
                    visible: {
                        var count = 0
                        for (var i = 0; i < uigraph.selectedNodes.count; ++i) {
                            var node = uigraph.selectedNodes.at(i)
                            if (node && !node.isComputable)
                                return false
                            count += 1
                        }
                        return count > 0 || uigraph.canSubmit
                    }
                    height: visible ? implicitHeight : 0

                    enabled: {
                        var canSubmit = false
                        for (var i = 0; i < uigraph.selectedNodes.count; ++i) {
                            var node = uigraph.selectedNodes.at(i)
                            if (!node)
                                continue
                            if (uigraph.graph.canComputeTopologically(node)) {
                                if (nodeMenu.isComputed) {
                                    canSubmit = true
                                } else if (uigraph.graph.canSubmitOrCompute(node) > 1) {
                                    canSubmit = true
                                }
                            }
                        }
                        return canSubmit
                    }
                    onTriggered: {
                        if (nodeMenu.isComputed) {
                            resubmit = true
                            deleteDataMenuItem.showConfirmationDialog(false)
                        } else {
                            submitRequest(uigraph.selectedNodes)
                        }
                    }
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
                    visible: nodeMenu.currentNode ? nodeMenu.currentNode.isComputable : false
                    height: visible ? implicitHeight : 0
                    onTriggered: Qt.openUrlExternally(Filepath.stringToUrl(nodeMenu.currentNode.internalFolder))
                }
                MenuSeparator {
                    visible: nodeMenu.currentNode ? nodeMenu.currentNode.isComputable : false
                }
                MenuItem {
                    text: "Cut Node(s)"
                    enabled: true
                    ToolTip.text: "Copy selection to the clipboard and remove it"
                    ToolTip.visible: hovered
                    onTriggered: {
                        copyNodes()
                        uigraph.removeNodes(uigraph.selectedNodes)
                    }
                }
                MenuItem {
                    text: "Copy Node(s)"
                    enabled: true
                    ToolTip.text: "Copy selection to the clipboard"
                    ToolTip.visible: hovered
                    onTriggered: copyNodes()
                }
                MenuItem {
                    text: "Paste Node(s)"
                    enabled: true
                    ToolTip.text: "Copy selection to the clipboard and immediately paste it"
                    ToolTip.visible: hovered
                    onTriggered: {
                        copyNodes()
                        pasteNodes()
                    }
                }
                MenuItem {
                    text: "Duplicate Node(s)" + (duplicateFollowingButton.hovered ? " From Here" : "")
                    enabled: true
                    onTriggered: duplicateNode(false)
                    MaterialToolButton {
                        id: duplicateFollowingButton
                        height: parent.height
                        anchors {
                            right: parent.right
                            rightMargin: parent.padding
                        }
                        text: MaterialIcons.fast_forward
                        onClicked: {
                            duplicateNode(true)
                            nodeMenu.close()
                        }
                    }
                }
                MenuItem {
                    text: "Remove Node(s)" + (removeFollowingButton.hovered ? " From Here" : "")
                    enabled: nodeMenu.currentNode ? !nodeMenu.currentNode.locked : false
                    onTriggered: uigraph.removeNodes(uigraph.selectedNodes)
                    MaterialToolButton {
                        id: removeFollowingButton
                        height: parent.height
                        anchors {
                            right: parent.right
                            rightMargin: parent.padding
                        }
                        text: MaterialIcons.fast_forward
                        onClicked: {
                            uigraph.removeNodesFrom(uigraph.selectedNodes)
                            nodeMenu.close()
                        }
                    }
                }
                MenuSeparator {
                    visible: nodeMenu.currentNode ? nodeMenu.currentNode.isComputable : false
                }
                MenuItem {
                    id: deleteDataMenuItem
                    text: "Delete Data" + (deleteFollowingButton.hovered ? " From Here" : "" ) + "..."
                    visible: nodeMenu.currentNode ? nodeMenu.currentNode.isComputable : false
                    height: visible ? implicitHeight : 0
                    enabled: {
                        if (!nodeMenu.currentNode)
                            return false
                        // Check if the current node is locked (needed because it does not belong to its own duplicates list)
                        if (nodeMenu.currentNode.locked)
                            return false
                        // Check if at least one of the duplicate nodes is locked
                        for (let i = 0; i < nodeMenu.currentNode.duplicates.count; ++i) {
                            if (nodeMenu.currentNode.duplicates.at(i).locked)
                                return false
                        }
                        return true
                    }

                    function showConfirmationDialog(deleteFollowing) {
                        uigraph.forceNodesStatusUpdate()
                        var obj = deleteDataDialog.createObject(root,
                                           {
                                               "node": nodeMenu.currentNode,
                                               "deleteFollowing": deleteFollowing
                                           })
                        obj.open()
                        nodeMenu.close()
                    }

                    onTriggered: showConfirmationDialog(false)

                    MaterialToolButton {
                        id: deleteFollowingButton
                        anchors {
                            right: parent.right
                            rightMargin: parent.padding
                        }
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

                            text: "Delete Data of '" + node.label + "'" + (uigraph.selectedNodes.count > 1 ? " and other selected Nodes" : "") + (deleteFollowing ?  " and following Nodes?" : "?")
                            helperText: "Warning: This operation cannot be undone."
                            standardButtons: Dialog.Yes | Dialog.Cancel

                            onAccepted: {
                                if (deleteFollowing)
                                    uigraph.clearDataFrom(uigraph.selectedNodes)
                                else
                                    uigraph.clearData(uigraph.selectedNodes)

                                root.dataDeleted()
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
                property var temporaryEdgeAboutToBeRemoved: undefined

                delegate: Node {
                    id: nodeDelegate

                    node: object
                    width: uigraph.layout.nodeWidth

                    mainSelected: uigraph.selectedNode === node
                    selected: uigraph.selectedNodes.contains(node)
                    hovered: uigraph.hoveredNode === node

                    onAttributePinCreated: function(attribute, pin) { registerAttributePin(attribute, pin) }
                    onAttributePinDeleted: function(attribute, pin) { unregisterAttributePin(attribute, pin) }

                    onPressed: function(mouse) {
                        if (mouse.button === Qt.LeftButton) {
                            if (mouse.modifiers & Qt.ControlModifier && !(mouse.modifiers & Qt.AltModifier)) {
                                if (mainSelected && selected) {
                                    // Left clicking a selected node twice with control will deselect it
                                    uigraph.selectedNodes.remove(node)
                                    uigraph.selectedNodesChanged()
                                    selectNode(null)
                                    return
                                }
                            } else if (mouse.modifiers & Qt.AltModifier) {
                                if (!(mouse.modifiers & Qt.ControlModifier)) {
                                    uigraph.clearNodeSelection()
                                }
                                uigraph.selectFollowing(node)
                            } else if (!mainSelected && !selected) {
                                uigraph.clearNodeSelection()
                            }
                        } else if (mouse.button === Qt.RightButton) {
                            if (!mainSelected && !selected) {
                                uigraph.clearNodeSelection()
                            }
                            nodeMenu.currentNode = node
                            nodeMenu.popup()
                        }
                        selectNode(node)
                    }

                    onDoubleClicked: function(mouse) { root.nodeDoubleClicked(mouse, node) }

                    onMoved: function(position) { uigraph.moveNode(node, position, uigraph.selectedNodes) }

                    onEntered: uigraph.hoveredNode = node
                    onExited: uigraph.hoveredNode = null

                    onEdgeAboutToBeRemoved: function(input) {
                        /*
                         * Sometimes the signals are not in the right order because of weird Qt/QML update order
                         * (next DropArea entered signal before previous DropArea exited signal) so edgeAboutToBeRemoved
                         * must be set to undefined before it can be set to another attribute object.
                         */
                        if (input === undefined) {
                            if (nodeRepeater.temporaryEdgeAboutToBeRemoved === undefined) {
                                root.edgeAboutToBeRemoved = input
                            } else {
                                root.edgeAboutToBeRemoved = nodeRepeater.temporaryEdgeAboutToBeRemoved
                                nodeRepeater.temporaryEdgeAboutToBeRemoved = undefined
                            }
                        } else {
                            if (root.edgeAboutToBeRemoved === undefined) {
                                root.edgeAboutToBeRemoved = input
                            } else {
                                nodeRepeater.temporaryEdgeAboutToBeRemoved = input
                            }
                        }
                    }

                    onPositionChanged: {
                        if (dragging && uigraph.selectedNodes.contains(node)) {
                            // Update all selected nodes positions with this node that is being dragged
                            for (var i = 0; i < nodeRepeater.count; i++) {
                                var otherNode = nodeRepeater.itemAt(i)
                                if (uigraph.selectedNodes.contains(otherNode.node) && otherNode.node !== node) {
                                    otherNode.x = otherNode.node.x + (x - node.x)
                                    otherNode.y = otherNode.node.y + (y - node.y)
                                }
                            }
                        }
                    }

                    // Allow all nodes to know if they are being dragged
                    onDraggingChanged: nodeRepeater.dragging = dragging

                    // Must not be enabled during drag because the other nodes will be slow to match the movement of the node being dragged
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

        DropArea {
            id: dropArea
            anchors.fill: parent
            keys: ["text/uri-list"]
            onEntered: {
                nbMeshroomScenes = 0
                nbDraggedFiles = drag.urls.length

                drag.urls.forEach(function(file) {
                    if (file.endsWith(".mg")) {
                        nbMeshroomScenes++
                    }
                })
            }

            onDropped: function(drop) {
                if (nbMeshroomScenes == nbDraggedFiles || nbMeshroomScenes == 0) {
                    // Retrieve mouse position and convert coordinate system
                    // from pixel values to graph reference system
                    var mousePosition = mapToItem(draggable, drag.x, drag.y)
                    // Send the list of files,
                    // to create the corresponding nodes or open another scene
                    filesDropped(drop, mousePosition)
                } else {
                    errorDialog.open()
                }
            }
        }
    }

    MessageDialog {
        id: errorDialog

        icon.text: MaterialIcons.error
        icon.color: "#F44336"

        title: "Different File Types"
        text: "Do not mix .mg files and other types of files."
        standardButtons: Dialog.Ok

        parent: Overlay.overlay

        onAccepted: close()
    }

    // Toolbar
    FloatingPane {
        padding: 2
        anchors.bottom: parent.bottom
        RowLayout {
            id: navigation
            spacing: 4

            // Default index for search
            property int currentIndex: -1
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
                            implicitWidth: 85
                            currentIndex: uigraph ? uigraph.layout.depthMode : -1
                            onActivated: {
                                uigraph.layout.depthMode = currentIndex
                            }
                        }
                    }
                }
            }

            // Search nodes in the graph
            SearchBar {
                id: graphSearchBar
  
                toggle: true // enable toggling the actual text field by the search button
                Layout.minimumWidth: graphSearchBar.width
                maxWidth: 150

                textField.background.opacity: 0.5
                textField.onTextChanged: navigation.currentIndex = -1

                onReturnPressed: {
                    nextArrow.clicked()
                }
            }

            MaterialToolButton {
                text: MaterialIcons.arrow_left
                padding: 0
                visible: graphSearchBar.text !== ""
                onClicked: {
                    navigation.currentIndex--
                    if (navigation.currentIndex === -1)
                        navigation.currentIndex = filteredNodes.count - 1
                    navigation.nextItem()
                }
            }

            MaterialToolButton {
                id: nextArrow
                text: MaterialIcons.arrow_right
                padding: 0
                visible: graphSearchBar.text !== ""
                onClicked: {
                    navigation.currentIndex++
                    if (navigation.currentIndex === filteredNodes.count)
                        navigation.currentIndex = 0
                    navigation.nextItem()
                }
            }

            Label {
                id: currentSearchLabel
                text: " " + (navigation.currentIndex + 1) + "/" + filteredNodes.count
                padding: 0
                visible: graphSearchBar.text !== ""
            }

            Repeater {
                id: filteredNodes
                model: SortFilterDelegateModel {
                    model: root.graph ? root.graph.nodes : undefined
                    sortRole: "label"
                    filters: [{role: "label", value: graphSearchBar.text}]
                    delegate: Item {
                        property var index_: index
                    }
                    function modelData(item, roleName_) {
                        return item.model.object[roleName_]
                    }
                }
            }

            function nextItem() {
                // compute bounding box
                var node = nodeRepeater.itemAt(filteredNodes.itemAt(navigation.currentIndex).index_)
                var bbox = Qt.rect(node.x, node.y, node.width, node.height)
                // rescale to fit the bounding box in the view, zoom is limited to prevent huge text
                draggable.scale = Math.min(Math.min(root.width / bbox.width, root.height / bbox.height),maxZoom)
                // recenter
                draggable.x = bbox.x*draggable.scale * -1 + (root.width - bbox.width * draggable.scale) * 0.5
                draggable.y = bbox.y*draggable.scale * -1 + (root.height - bbox.height * draggable.scale) * 0.5
            }
        }
    }

    function registerAttributePin(attribute, pin) {
        root._attributeToDelegate[attribute] = pin
    }

    function unregisterAttributePin(attribute, pin) {
        delete root._attributeToDelegate[attribute]
    }

    function boundingBox() {
        var first = nodeRepeater.itemAt(0)
        if (first === null) {
            return Qt.rect(0, 0, 0, 0)
        }
        var bbox = Qt.rect(first.x, first.y, first.x + first.width, first.y + first.height)
        for (var i = 0; i < root.graph.nodes.count; ++i) {
            var item = nodeRepeater.itemAt(i)
            bbox.x = Math.min(bbox.x, item.x)
            bbox.y = Math.min(bbox.y, item.y)
            bbox.width = Math.max(bbox.width, item.x + item.width)
            bbox.height = Math.max(bbox.height, item.y + item.height)
        }
        bbox.width -= bbox.x
        bbox.height -= bbox.y
        return bbox;
    }

    // Fit graph to fill root
    function fit() {
        // Compute bounding box
        var bbox = boundingBox()
        // Rescale to fit the bounding box in the view, zoom is limited to prevent huge text
        draggable.scale = Math.min(Math.min(root.width / bbox.width, root.height / bbox.height), maxZoom)
        // Recenter
        draggable.x = bbox.x * draggable.scale * -1 + (root.width - bbox.width * draggable.scale) * 0.5
        draggable.y = bbox.y * draggable.scale * -1 + (root.height - bbox.height * draggable.scale) * 0.5
    }
}
