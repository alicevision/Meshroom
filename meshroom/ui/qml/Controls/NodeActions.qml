import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import MaterialIcons 2.2
import Utils 1.0

Item {
    id: root
    
    // Settings
    property real headerOffset: 10   // Distance above the node in screen pixels
    property real _opacity: 0.9

    // Objects passed from the graph editor
    property var uigraph: null
    property var draggable: null     // The draggable container from GraphEditor
    property var nodeRepeater: null  // Reference to nodeRepeater to find delegates

    // Signals
    signal computeRequest(var node)
    signal stopComputeRequest(var node)
    signal reComputeRequest(var node)
    signal submitRequest(var node)
    signal reSubmitRequest(var node)
    
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
    
    Rectangle {
        id: actionHeader

        readonly property bool hasSelectedNode: uigraph && uigraph.nodeSelection.selectedIndexes.length === 1
        readonly property var selectedNode: hasSelectedNode ? uigraph.selectedNode : null
        readonly property var selectedNodeDelegate: selectedNode ? root.nodeDelegate(selectedNode) : null

        visible: selectedNodeDelegate !== null
        color: "transparent"
        width: actionItemsRow.width
        height: actionItemsRow.height

        // State properties 
        property string currentExecMode: selectedNode ? selectedNode.globalExecMode : "NONE"
        property string currentStatus: selectedNode ? selectedNode.globalStatus : "NONE"
        property bool nodeCanBeStopped: selectedNode ? selectedNode.canBeStopped() : false
        property bool nodeIsExternal: selectedNode ? selectedNode.isExternal : false
        property bool nodeLocked: selectedNode ? selectedNode.locked : false

        // Derived values
        readonly property bool runningExternally: currentExecMode === "EXTERN"
                                                  && ["SUBMITTED", "RUNNING"].includes(currentStatus)
        readonly property bool stoppable: selectedNode && currentStatus === "RUNNING" && nodeCanBeStopped
        readonly property bool launchable: selectedNode &&
                                           (nodeCanBeStopped || ["NONE","STOPPED","KILLED","ERROR"].includes(currentStatus))

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
        
        // Set initial position
        onSelectedNodeDelegateChanged: updatePosition()

        // Listen to updates to status
        Connections {
            target: actionHeader.selectedNode
            function onGlobalStatusChanged()   { actionHeader.currentStatus = target.globalStatus }
            function onGlobalExecModeChanged() { actionHeader.currentExecMode = target.globalExecMode }
            function onIsComputedChanged()     { actionHeader.nodeCanBeStopped = target.canBeStopped() }
            function onLockedChanged()         { actionHeader.nodeLocked = target.locked }
            ignoreUnknownSignals: true
        }

        // Also listen to uigraph for status updates
        Connections {
            target: root.uigraph
            function onComputationStatusChanged() { 
                actionHeader.currentStatus = actionHeader.selectedNode ? actionHeader.selectedNode.globalStatus : "NONE"
            }
            function onNodeStatusUpdated() {
                actionHeader.currentStatus = actionHeader.selectedNode ? actionHeader.selectedNode.globalStatus : "NONE"
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
                text: actionHeader.stoppable ? MaterialIcons.cancel_schedule_send : MaterialIcons.send
                padding: 6
                ToolTip.text: "Start/Stop Compute"
                ToolTip.visible: hovered
                ToolTip.delay: 1000
                enabled: actionHeader.selectedNode && actionHeader.launchable
                background: Rectangle {
                    color: {
                        if (!computeButton.enabled) return activePalette.button
                        if (actionHeader.currentStatus === "RUNNING") {
                            if (computeButton.hovered) return Colors.statusColors["STOPPED"]
                            return Qt.darker(Colors.statusColors["STOPPED"], 1.3)
                        } else {
                            if (computeButton.hovered) return activePalette.highlight
                            return activePalette.button
                        }
                    }
                    opacity: computeButton.hovered ? 1 : root._opacity
                    border.color: computeButton.hovered ? activePalette.highlight : Qt.darker(activePalette.window, 1.3)
                    border.width: 1
                    radius: 3
                }
                onClicked: {
                    if (actionHeader.selectedNode && !actionHeader.nodeIsExternal && actionHeader.currentStatus === "RUNNING") {
                        root.stopComputeRequest(actionHeader.selectedNode)
                    } else {
                        root.computeRequest(actionHeader.selectedNode)
                    }
                }
            }
            
            // Re-compute button : stop local process and relaunch locally 
            MaterialToolButton {
                id: reComputeButton
                font.pointSize: 16
                text: MaterialIcons.autorenew
                padding: 6
                ToolTip.text: "Re-compute"
                ToolTip.visible: hovered
                ToolTip.delay: 1000
                enabled: actionHeader.selectedNode && !actionHeader.runningExternally
                background: Rectangle {
                    color: {
                        if (!reComputeButton.enabled) return activePalette.button
                        if (reComputeButton.hovered) return activePalette.highlight
                        return activePalette.button
                    }
                    opacity: reComputeButton.hovered ? 1 : root._opacity
                    border.color: reComputeButton.hovered ? activePalette.highlight : Qt.darker(activePalette.window, 1.3)
                    border.width: 1
                    radius: 3
                }
                onClicked: {
                    if (actionHeader.selectedNode) {
                        root.reComputeRequest(actionHeader.selectedNode)
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
                enabled: actionHeader.selectedNode ? !actionHeader.nodeLocked : false
                background: Rectangle {
                    color: {
                        if (!submitButton.enabled) return activePalette.button
                        if (actionHeader.runningExternally) return Colors.statusColors["SUBMITTED"]
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
            
            // Re-submit button : stop everything and relaunch on farm
            // TODO : disabled for now because we can't stop jobs submitted on farm
            MaterialToolButton {
                id: reSubmitButton
                font.pointSize: 16
                text: MaterialIcons.double_arrow
                padding: 6
                ToolTip.text: "Re-submit on Render Farm"
                ToolTip.visible: hovered
                ToolTip.delay: 1000
                visible: false  // root.uigraph ? root.uigraph.canSubmit : false
                enabled: actionHeader.selectedNode !== null
                background: Rectangle {
                    color: {
                        if (!actionHeader.selectedNode) return activePalette.button
                        if (reSubmitButton.hovered) return activePalette.highlight
                        return activePalette.button
                    }
                    opacity: reSubmitButton.hovered ? 1 : root._opacity
                    border.color: reSubmitButton.hovered ? activePalette.highlight : Qt.darker(activePalette.window, 1.3)
                    border.width: 1
                    radius: 3
                }
                onClicked: {
                    if (actionHeader.selectedNode) {
                        root.reSubmitRequest(actionHeader.selectedNode)
                    }
                }
            }
        }
    }
}