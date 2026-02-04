import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import MaterialIcons 2.2
import Utils 1.0

Item {
    id: root
    
    // Settings
    readonly property real headerOffset: 10   // Distance above the node in screen pixels
    readonly property real _opacity: 0.9

    // Objects passed from the graph editor
    property var uigraph: null
    property var draggable: null     // The draggable container from GraphEditor
    property var nodeRepeater: null  // Reference to nodeRepeater to find delegates

    // Signals
    signal computeRequest(var node)      // Start local computation
    signal stopComputeRequest(var node)  // Stop local computation
    signal deleteDataRequest(var node)   // Delete node data
    signal submitRequest(var node)       // Start external computation (submission on farm)
    signal stopSubmitRequest(var node)   // Stop external computation (interrupt tasks on farm)
    signal retrySubmitRequest(var node)  // Retry error tasks on farm
    
    SystemPalette { id: activePalette }

    /**
      * Get the node delegate
      */
    function nodeDelegate(node) {
        if (!nodeRepeater) 
            return null
        for (var i = 0; i < nodeRepeater.count; ++i) {
            if (nodeRepeater.getItemAt(i).node === node)
                return nodeRepeater.getItemAt(i)
        }
        return null
    }

    enum ButtonState {
        DISABLED   = 0,
        LAUNCHABLE = 1,
        DELETABLE  = 2,
        STOPPABLE  = 3
    }

    Rectangle {
        id: actionHeader

        readonly property bool hasSelectedNode: uigraph && uigraph.nodeSelection.selectedIndexes.length === 1
        readonly property var selectedNode: hasSelectedNode ? uigraph.selectedNode : null
        readonly property var selectedNodeDelegate: selectedNode ? root.nodeDelegate(selectedNode) : null

        visible: selectedNodeDelegate !== null
        color: "transparent"
        width: actionItemsRow.width
        height: actionItemsRow.height

        // 
        // ===== Manage NodeActions position =====
        // 

        // Prevents losing focus on the node when we click on buttons of the actionItems
        MouseArea {
            anchors.fill: parent
            onPressed:       function(mouse) { mouse.accepted = true }
            onReleased:      function(mouse) { mouse.accepted = true }
            onClicked:       function(mouse) { mouse.accepted = true }
            onDoubleClicked: function(mouse) { mouse.accepted = true }
            hoverEnabled: false
        }

        function keepNodeActionOnWindow() {
            if (x < 0) {
                x = 0
            }
            if (y < 0) {
                y = 0
            }
        }

        // Update position
        function updatePosition() {
            if (width == 0 && height == 0) {  
                actionItemsRow.visible = true  
                return  
            } else if (width == 0 || height == 0) {  
                actionItemsRow.visible = false  
                return  
            }  
            actionItemsRow.visible = true  

            if (!selectedNodeDelegate || !draggable) return
            // Calculate node position in screen coordinates
            const nodeScreenX = selectedNodeDelegate.x * draggable.scale + draggable.x
            const nodeScreenY = selectedNodeDelegate.y * draggable.scale + draggable.y
            // Position header above the node (fixed offset in screen pixels)
            x = nodeScreenX + (selectedNodeDelegate.width * draggable.scale - width) / 2
            y = nodeScreenY - height - headerOffset
            // keepNodeActionOnWindow()
        }

        onHeightChanged: {
            actionHeader.updatePosition()
        }

        onWidthChanged: {
            actionHeader.updatePosition()
        }

        // Update position when the user moves on the graph
        Connections {
            target: root.draggable
            function onXChanged()     { Qt.callLater(actionHeader.updatePosition) }
            function onYChanged()     { Qt.callLater(actionHeader.updatePosition) }
            function onScaleChanged() { Qt.callLater(actionHeader.updatePosition) }
        }

        // Update position when nodes are moved
        Connections {
            target: actionHeader.selectedNodeDelegate
            function onXChanged() { actionHeader.updatePosition() }
            function onYChanged() { actionHeader.updatePosition() }
            ignoreUnknownSignals: true
        }

        // 
        // ===== Manage buttons =====
        // 

        property bool nodeIsLocked: false
        property bool canComputeNode: false
        property bool canStopNode: false
        property bool canRestartNode: false  // Node can be restarted, locally or externally
        property bool canSubmitNode: false
        property bool nodeSubmitted: false
        property bool canRetryNode: false    // Error tasks can be restarted for external node

        property int computeButtonState: NodeActions.ButtonState.LAUNCHABLE
        property string computeButtonIcon: {
            switch (computeButtonState) {
                case NodeActions.ButtonState.STOPPABLE: return MaterialIcons.cancel_schedule_send
                default: return MaterialIcons.send
            }
        }
        property string computeButtonTooltip: {
            switch (computeButtonState) {
                case NodeActions.ButtonState.STOPPABLE: return "Stop Compute"
                default: return "Start Compute"
            }
        }

        property int submitButtonState: NodeActions.ButtonState.LAUNCHABLE
        property string submitButtonIcon: {
            switch (submitButtonState) {
                case NodeActions.ButtonState.STOPPABLE: return MaterialIcons.paragliding
                default: return MaterialIcons.rocket_launch
            }
        }
        property string submitButtonTooltip: {
            switch (submitButtonState) {
                case NodeActions.ButtonState.STOPPABLE: return "Interrupt Job on Render Farm"
                default: return "Submit on Render Farm"
            }
        }

        function getComputeButtonState(node) {
            if (actionHeader.canStopNode)
                return NodeActions.ButtonState.STOPPABLE
            if (!actionHeader.nodeIsLocked && node.globalStatus == "SUCCESS")
                return NodeActions.ButtonState.DELETABLE
            if (actionHeader.canComputeNode)
                return NodeActions.ButtonState.LAUNCHABLE
            return NodeActions.ButtonState.DISABLED
        }

        function getSubmitButtonState(node) {
            if (actionHeader.canStopNode)
                return NodeActions.ButtonState.STOPPABLE
            if (!actionHeader.nodeIsLocked && node.globalStatus == "SUCCESS")
                return NodeActions.ButtonState.DELETABLE
            if (actionHeader.canSubmitNode)
                return NodeActions.ButtonState.LAUNCHABLE
            return NodeActions.ButtonState.DISABLED
        }
        
        function isSubmittedExternally(node) {
            return node.globalExecMode == "EXTERN" && ["RUNNING", "SUBMITTED"].includes(node.globalStatus)
        }
        
        function isNodeRestartable(node) {
            return actionHeader.computeButtonState == NodeActions.ButtonState.LAUNCHABLE && 
                ["ERROR", "STOPPED", "KILLED"].includes(node.globalStatus)
        }

        function isNodeRetriable(node) {
            return node.globalExecMode == "EXTERN" && ["ERROR", "STOPPED", "KILLED"].includes(node.globalStatus)
        }

        function updateProperties(node) {
            if (!node) return
            // Update properties values
            actionHeader.canComputeNode = uigraph.canComputeNode(node)
            actionHeader.canSubmitNode = uigraph.canSubmitNode(node)
            actionHeader.canStopNode = node.canBeStopped() || node.canBeCanceled()
            actionHeader.nodeIsLocked = node.locked
            actionHeader.nodeSubmitted = isSubmittedExternally(node)
            // Update button states
            actionHeader.computeButtonState = getComputeButtonState(node)
            actionHeader.submitButtonState = getSubmitButtonState(node)
            actionHeader.canRestartNode = isNodeRestartable(node)
            actionHeader.canRetryNode = isNodeRetriable(node)
        }

        // Set initial state & position
        onSelectedNodeDelegateChanged: {
            if (actionHeader.selectedNode) {
                actionHeader.updateProperties(actionHeader.selectedNode)
                Qt.callLater(actionHeader.updatePosition)
            }
        }

        // Listen to updates to status
        Connections {
            target: actionHeader.selectedNode
            function onGlobalStatusChanged() {
                actionHeader.updateProperties(target)
            }
            function onLockedChanged() { 
                actionHeader.nodeIsLocked = target.locked
            }
            ignoreUnknownSignals: true
        }

        // Listen to updates from nodes that are not selected
        Connections {
            target: root.uigraph
            function onComputingChanged() { 
                actionHeader.updateProperties(actionHeader.selectedNode)
            }
            ignoreUnknownSignals: true
        }

        Row {
            id: actionItemsRow
            anchors.centerIn: parent
            spacing: 2

            // Compute button
            MaterialToolButton {
                id: computeButton
                font.pointSize: 16
                text: actionHeader.computeButtonIcon
                padding: 6
                ToolTip.text: actionHeader.computeButtonTooltip
                ToolTip.visible: hovered
                ToolTip.delay: 1000
                visible: actionHeader.computeButtonState != NodeActions.ButtonState.DISABLED
                enabled: visible && !actionHeader.nodeSubmitted // Launchable & Stoppable, local
                // Icon color
                textColor: checked ? palette.highlight : palette.text
                // Background color
                background: Rectangle {
                    color: {
                        if (!computeButton.enabled)
                            return activePalette.button
                        if (actionHeader.computeButtonState == NodeActions.ButtonState.STOPPABLE)
                            return computeButton.hovered ? Colors.orange : Qt.darker(Colors.orange, 1.3)
                        return computeButton.hovered ? activePalette.highlight : activePalette.button
                    }
                    opacity: computeButton.hovered ? 1 : root._opacity
                    border.color: computeButton.hovered ? activePalette.highlight : Qt.darker(activePalette.window, 1.3)
                    border.width: 1
                    radius: 3
                }
                onClicked: {
                    switch (actionHeader.computeButtonState) {
                        case NodeActions.ButtonState.STOPPABLE:
                            root.stopComputeRequest(actionHeader.selectedNode)
                            break
                        case NodeActions.ButtonState.LAUNCHABLE:
                            root.computeRequest(actionHeader.selectedNode)
                            break
                        case NodeActions.ButtonState.DELETABLE:
                            root.deleteDataRequest(actionHeader.selectedNode)
                            root.computeRequest(actionHeader.selectedNode)
                            break
                        default:
                            break
                    }
                }
            }

            // Clear node
            MaterialToolButton {
                id: deleteDataButton
                font.pointSize: 16
                text: MaterialIcons.delete_
                padding: 6
                ToolTip.text: "Delete Data"
                ToolTip.visible: hovered
                ToolTip.delay: 1000
                visible: actionHeader.canRestartNode || actionHeader.computeButtonState == NodeActions.ButtonState.DELETABLE
                enabled: visible
                background: Rectangle {
                    color: computeButton.hovered ? Colors.red : Qt.darker(Colors.red, 1.3)
                    opacity: computeButton.hovered ? 1 : root._opacity
                    border.color: computeButton.hovered ? activePalette.highlight : Qt.darker(activePalette.window, 1.3)
                    border.width: 1
                    radius: 3
                }
                onClicked: {
                    root.deleteDataRequest(actionHeader.selectedNode)
                }
            }

            // Submit button
            MaterialToolButton {
                id: submitButton
                font.pointSize: 16
                text: actionHeader.submitButtonIcon
                padding: 6
                ToolTip.text: actionHeader.submitButtonTooltip
                ToolTip.visible: hovered
                ToolTip.delay: 1000
                visible: actionHeader.submitButtonState != NodeActions.ButtonState.DISABLED
                enabled: visible && (actionHeader.nodeSubmitted || !actionHeader.nodeIsLocked)  // Launchable & Stoppable, external
                // Icon color
                textColor: checked ? palette.highlight : palette.text
                // Background color
                background: Rectangle {
                    color: {
                        if (!submitButton.enabled)
                            return activePalette.button

                        if (actionHeader.submitButtonState == NodeActions.ButtonState.STOPPABLE)
                            return submitButton.hovered ? Colors.orange : Qt.darker(Colors.orange, 1.3)
                        return submitButton.hovered ? activePalette.highlight : activePalette.button
                    }
                    opacity: submitButton.hovered ? 1 : root._opacity
                    border.color: submitButton.hovered ? activePalette.highlight : Qt.darker(activePalette.window, 1.3)
                    border.width: 1
                    radius: 3
                }
                onClicked: {
                    switch (actionHeader.submitButtonState) {
                        case NodeActions.ButtonState.STOPPABLE:
                            root.stopSubmitRequest(actionHeader.selectedNode)
                            break
                        case NodeActions.ButtonState.LAUNCHABLE:
                            root.submitRequest(actionHeader.selectedNode)
                            actionHeader.updateProperties(actionHeader.selectedNode)
                            break
                        case NodeActions.ButtonState.DELETABLE:
                            root.deleteDataRequest(actionHeader.selectedNode)
                            root.submitRequest(actionHeader.selectedNode)
                            break
                        default:
                            break
                    }
                }
            }

            // Retry button (for farm submissions that have failed)
            MaterialToolButton {
                id: retryButton
                font.pointSize: 16
                text: MaterialIcons.cloud_sync
                padding: 6
                ToolTip.text: "Retry Submission On Render Farm"
                ToolTip.visible: hovered
                ToolTip.delay: 1000
                visible: actionHeader.canRetryNode
                enabled: visible

                // Background color
                background: Rectangle {
                    color: {
                        return retryButton.hovered ? activePalette.highlight : activePalette.button
                    }
                    opacity: retryButton.hovered ? 1 : root._opacity
                    border.color: retryButton.hovered ? activePalette.highlight : Qt.darker(activePalette.window, 1.3)
                    border.width: 1
                    radius: 3
                }

                onClicked: {
                    root.retrySubmitRequest(actionHeader.selectedNode)
                }
            }
        }
    }
}