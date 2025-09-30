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
        LAUNCHABLE,
        STOPPABLE,
        DELETABLE,
        DISABLED
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
        property bool submittedExternally: false
        property int computeButtonState: NodeActions.ButtonState.LAUNCHABLE
        property string computeButtonIcon: {
            switch (computeButtonState) {
                case NodeActions.ButtonState.STOPPABLE: return MaterialIcons.cancel_schedule_send
                case NodeActions.ButtonState.DELETABLE: return MaterialIcons.delete_
                default: return MaterialIcons.send
            }
        }
        property int submitButtonState: NodeActions.ButtonState.LAUNCHABLE

        function getComputeButtonState(node) {
            if (!node.isComputableType || node.isCompatibilityNode)
                return NodeActions.ButtonState.DISABLED
            if (node.canBeStopped()) return NodeActions.ButtonState.STOPPABLE
            if (node.canBeCanceled()) return NodeActions.ButtonState.STOPPABLE
            if (actionHeader.nodeIsLocked) return NodeActions.ButtonState.DISABLED
            switch (node.globalStatus) {
                case "NONE":
                case "ERROR":
                case "STOPPED":
                case "KILLED":
                    return NodeActions.ButtonState.LAUNCHABLE
                case "SUCCESS":
                    return NodeActions.ButtonState.DELETABLE
            }
            return NodeActions.ButtonState.DISABLED
        }

        function getSubmitButtonState(node) {
            if (!node.isComputableType || node.isCompatibilityNode)
                return NodeActions.ButtonState.DISABLED
            if (actionHeader.nodeIsLocked || node.canBeStopped()) {
                return NodeActions.ButtonState.DISABLED
            }
            switch (node.globalStatus) {
                case "NONE":
                case "ERROR":
                case "STOPPED":
                case "KILLED":
                case "SUCCESS":
                    return NodeActions.ButtonState.LAUNCHABLE
                    return NodeActions.ButtonState.LAUNCHABLE
                    break
                // SUBMITTED / RUNNING / INPUT -> DISABLED
            }
            return NodeActions.ButtonState.DISABLED
        }
        
        function isSubmittedExternally(node) {
            if (node.globalExecMode == "EXTERN" && node.globalStatus == "SUBMITTED")
                return true
            return false
        }

        function updateProperties(node) {
            actionHeader.nodeIsLocked = node.locked
            actionHeader.computeButtonState = getComputeButtonState(node)
            actionHeader.submitButtonState = getSubmitButtonState(node)
            actionHeader.submittedExternally = isSubmittedExternally(node)
        }


        // Set initial state & position
        onSelectedNodeDelegateChanged: {
            updatePosition()
            if (actionHeader.selectedNode) {
                actionHeader.updateProperties(actionHeader.selectedNode)
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
                ToolTip.text: "Start/Stop Compute"
                ToolTip.visible: hovered
                ToolTip.delay: 1000
                enabled: actionHeader.computeButtonState != NodeActions.ButtonState.DISABLED
                background: Rectangle {
                    color: {
                        if (!computeButton.enabled) return activePalette.button
                        switch (actionHeader.computeButtonState) {
                            case NodeActions.ButtonState.STOPPABLE:
                                if (computeButton.hovered) return Colors.orange
                                return Qt.darker(Colors.orange, 1.3)
                            case NodeActions.ButtonState.DELETABLE:
                                if (computeButton.hovered) return Colors.red
                                return Qt.darker(Colors.red, 1.3)
                            default: break
                        }
                        if (computeButton.hovered) return activePalette.highlight
                        return activePalette.button
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
                            break
                        default: break
                    }
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
                // enabled: actionHeader.selectedNode ? !actionHeader.nodeLocked : false
                background: Rectangle {
                    color: {
                        if (actionHeader.submittedExternally) 
                            return Qt.darker(Colors.statusColors["SUBMITTED"], 1.2)
                        if (!submitButton.enabled) return activePalette.button
                        if (submitButton.hovered) return activePalette.highlight
                        return activePalette.button
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