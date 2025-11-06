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
    signal computeRequest(var node)
    signal stopComputeRequest(var node)
    signal deleteDataRequest(var node)
    signal submitRequest(var node)
    
    SystemPalette { id: activePalette }

    /**
      * Get the node delegate
      */
    function nodeDelegate(node) {
        if (!nodeRepeater) 
            return null
        for (var i = 0; i < nodeRepeater.count; ++i) {
            if (nodeRepeater.itemAt(i).node === node)
                return nodeRepeater.itemAt(i)
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

        // Update position
        function updatePosition() {
            if (!selectedNodeDelegate || !draggable) return
            // Calculate node position in screen coordinates
            const nodeScreenX = selectedNodeDelegate.x * draggable.scale + draggable.x
            const nodeScreenY = selectedNodeDelegate.y * draggable.scale + draggable.y
            // Position header above the node (fixed offset in screen pixels)
            x = nodeScreenX + (selectedNodeDelegate.width * draggable.scale - width) / 2
            y = nodeScreenY - height - headerOffset
            if (y < 0) {
                y = 0
            }
        }

        onWidthChanged: {
            updatePosition()
        }

        // Update position when the user moves on the graph
        Connections {
            target: root.draggable
            function onXChanged()     { actionHeader.updatePosition() }
            function onYChanged()     { actionHeader.updatePosition() }
            function onScaleChanged() { actionHeader.updatePosition() }
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
        property bool canRestartNode: false
        property bool canSubmitNode: false
        property bool nodeSubmitted: false

        property int computeButtonState: NodeActions.ButtonState.LAUNCHABLE
        property string computeButtonIcon: {
            switch (computeButtonState) {
                case NodeActions.ButtonState.STOPPABLE: return MaterialIcons.cancel_schedule_send
                default: return MaterialIcons.send
            }
        }
        property int submitButtonState: NodeActions.ButtonState.LAUNCHABLE

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
            if (actionHeader.nodeIsLocked || actionHeader.canStopNode)
                return NodeActions.ButtonState.DISABLED
            if (!actionHeader.nodeIsLocked && node.globalStatus == "SUCCESS")
                return NodeActions.ButtonState.DISABLED
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
                ToolTip.text: "Start/Stop/Restart Compute"
                ToolTip.visible: hovered
                ToolTip.delay: 1000
                visible: actionHeader.computeButtonState != NodeActions.ButtonState.DELETABLE
                enabled: actionHeader.computeButtonState % 2 == 1  // Launchable & Stoppable
                // Icon color
                textColor: (!enabled && actionHeader.nodeSubmitted) ? Colors.statusColors["SUBMITTED"] : (checked ? palette.highlight : palette.text)
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
                    }
                }
            }

            // Clear node
            MaterialToolButton {
                id: deleteDataButton
                font.pointSize: 16
                text: MaterialIcons.delete_
                padding: 6
                ToolTip.text: "Delete data"
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
                text: MaterialIcons.rocket_launch
                padding: 6
                ToolTip.text: "Submit on Render Farm"
                ToolTip.visible: hovered
                ToolTip.delay: 1000
                visible: root.uigraph ? root.uigraph.canSubmit : false
                enabled: actionHeader.submitButtonState != NodeActions.ButtonState.DISABLED
                // Icon color
                textColor: (!enabled && actionHeader.nodeSubmitted) ? Colors.statusColors["SUBMITTED"] : (checked ? palette.highlight : palette.text)
                // Background color
                background: Rectangle {
                    color: {
                        if (!submitButton.enabled)
                            return activePalette.button
                        return submitButton.hovered ? activePalette.highlight : activePalette.button
                    }
                    opacity: submitButton.hovered ? 1 : root._opacity
                    border.color: submitButton.hovered ? activePalette.highlight : Qt.darker(activePalette.window, 1.3)
                    border.width: 1
                    radius: 3
                }
                onClicked: {
                    if (actionHeader.selectedNode) {
                        root.submitRequest(actionHeader.selectedNode)
                    }
                }
            }
        }
    }
}