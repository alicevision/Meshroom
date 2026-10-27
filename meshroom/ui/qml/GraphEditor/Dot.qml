import QtQuick
import QtQuick.Controls

import Utils 1.0

/**
 * Visual representation of a Graph Dot Node.
 *
 * A Dot is a purely organizational pass-through node: it is drawn as a small circle
 * with a single pin acting as the anchor for both its "input" and "output" attributes,
 * so that edges look like they pass through a re-routing point.
 * Dragging the pin in the center of the dot creates an edge from its output; dragging
 * the border around the pin moves it. The label of the Dot is shown as a tooltip on hover.
 */
Item {
    id: root

    /// The underlying Node object
    property variant node
    /// Whether the node can be modified
    property bool readOnly: node ? node.locked : false

    // Mouse related states
    property bool mainSelected: false
    property bool selected: false
    property bool hovered: false
    property bool dragging: moveArea.drag.active
    // Combined x and y
    property point position: Qt.point(x, y)

    /// Diameter of the visual dot
    readonly property real dotSize: 14
    /// Size of the pin: same as regular attribute pins (see AttributePin.qml) - dragging it creates an edge
    readonly property real pinSize: 8
    /// Size of the (invisible) hit area: the border around the pin moves the Dot
    readonly property real hitSize: 40

    // Identifies this delegate as a dot node
    readonly property bool isDotNode: true

    // Mouse interaction related signals
    signal pressed(var mouse)
    signal released(var mouse)
    signal clicked(var mouse)
    signal doubleClicked(var mouse)
    signal moved(var position)
    signal entered()
    signal exited()

    // Already connected attribute with another edge in DropArea
    signal edgeAboutToBeRemoved(var input)

    // Emitted when the attribute pin is created
    signal attributePinCreated(var attribute, var pin)
    // Emitted when the attribute pin is deleted
    signal attributePinDeleted(var attribute, var pin)

    // use node name as object name to simplify debugging
    objectName: node ? node.name : ""

    // initialize position with node coordinates
    x: root.node ? root.node.x : undefined
    y: root.node ? root.node.y : undefined

    width: hitSize
    height: hitSize

    Connections {
        target: root.node

        function onPositionChanged() {
            root.x = root.node.x
            root.y = root.node.y
        }
    }

    /**
     * Redirect an ongoing edge drag (started from 'connector') to this Dot: the preview edge
     * is drawn from the Dot and follows the dragged connector, so that the drag appears to
     * continue from the Dot output attribute.
     * Used by the GraphEditor "insert Dot while dragging an edge" shortcut.
     */
    function redirectEdgeDrag(connector) {
        pin.redirectSource = connector
        pin.updateRedirectPosition()
    }

    // The Dot label is displayed as a tooltip (rename it from the Node Editor header)
    ToolTip {
        text: node ? node.label : ""
        visible: root.hovered && text !== ""
        delay: 500
    }

    // Dragging the border of the Dot moves it (the pin in the center creates edges)
    MouseArea {
        id: moveArea
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        hoverEnabled: true
        drag.target: root
        drag.threshold: 2
        onPressed: function(mouse) { root.pressed(mouse) }
        onReleased: function(mouse) { root.released(mouse) }
        onClicked: function(mouse) { root.clicked(mouse) }
        onDoubleClicked: function(mouse) { root.doubleClicked(mouse) }
        onEntered: root.entered()
        onExited: root.exited()
        drag.onActiveChanged: {
            if (!drag.active) {
                root.moved(Qt.point(root.x, root.y))
            }
        }
        cursorShape: drag.active ? Qt.ClosedHandCursor : Qt.OpenHandCursor
    }

    // The single pin of the Dot: it is registered for both the "input" and the "output"
    // attributes, so that incoming edges attach to inputAnchorPos and outgoing edges to
    // outputAnchorPos (both at the center of the dot).
    Item {
        id: pin
        anchors.centerIn: parent
        // Same size as regular attribute pins: only the pin creates edges, the border around it moves the Dot
        width: root.pinSize
        height: root.pinSize

        // Position of this pin in the 'draggable' coordinate space (see GraphEditor)
        property real globalX: root.x + x
        property real globalY: root.y + y

        // Edges attach at the center of the dot, for both directions
        readonly property point inputAnchorPos: Qt.point(width / 2, height / 2)
        readonly property point outputAnchorPos: Qt.point(width / 2, height / 2)

        property var inputAttribute: node ? node.attribute("input") : null
        property var outputAttribute: node ? node.attribute("output") : null
        readonly property bool connected: (inputAttribute && inputAttribute.hasAnyInputLinks) ||
                                           (outputAttribute && outputAttribute.hasAnyOutputLinks)

        /// The edge connector currently dragged from this pin (null if none)
        readonly property var draggedConnector: connectMA.drag.active ? outputDragTarget : null
        /// Connector whose ongoing edge drag is redirected to this Dot (insert Dot shortcut):
        /// the preview edge is drawn from the Dot and follows it, so that the drag appears
        /// to continue from the Dot output attribute
        property var redirectSource: null
        /// Whether this Dot's own edge drag has been redirected to another Dot
        readonly property bool dragRedirected: outputDragTarget.dragRedirectAttribute !== null

        Component.onCompleted: {
            if (pin.inputAttribute)
                root.attributePinCreated(pin.inputAttribute, pin)
            if (pin.outputAttribute)
                root.attributePinCreated(pin.outputAttribute, pin)
        }
        Component.onDestruction: {
            if (pin.inputAttribute)
                root.attributePinDeleted(pin.inputAttribute, pin)
            if (pin.outputAttribute)
                root.attributePinDeleted(pin.outputAttribute, pin)
        }

        // Follow a redirected drag: keep the connector (and thus the preview edge) under the mouse
        function updateRedirectPosition() {
            if (!redirectSource)
                return
            var pos = mapFromItem(redirectSource, redirectSource.width / 2, redirectSource.height / 2)
            outputDragTarget.x = pos.x - outputDragTarget.width / 2
            outputDragTarget.y = pos.y - outputDragTarget.height / 2
        }

        Connections {
            target: pin.redirectSource

            // The redirected drag is over: hide the preview and re-center the connector
            function onDraggingChanged() {
                if (pin.redirectSource && !pin.redirectSource.dragging) {
                    pin.redirectSource = null
                    outputDragTarget.x = pin.width / 2 - outputDragTarget.width / 2
                    outputDragTarget.y = pin.height / 2 - outputDragTarget.height / 2
                }
            }
            function onXChanged() { pin.updateRedirectPosition() }
            function onYChanged() { pin.updateRedirectPosition() }
        }

        // Visual dot (slightly larger than the pin, centered on it)
        Rectangle {
            id: dotCircle
            anchors.centerIn: parent
            width: root.dotSize
            height: root.dotSize
            radius: width / 2
            color: Colors.sysPalette.base
            border.width: 1
            border.color: {
                if (dropArea.acceptableDrop || root.hovered || root.mainSelected)
                    return Colors.sysPalette.highlight
                return Colors.sysPalette.mid
            }

            // Inner mark when the Dot passes a connection through
            Rectangle {
                anchors.centerIn: parent
                width: parent.width - 8
                height: parent.height - 8
                radius: width / 2
                visible: pin.connected
                color: {
                    if (dropArea.acceptableDrop || root.hovered || connectMA.drag.active)
                        return Colors.sysPalette.highlight
                    return Colors.sysPalette.text
                }
            }
        }

        // Selection ring
        Rectangle {
            anchors.fill: dotCircle
            anchors.margins: -2
            radius: width / 2
            visible: root.mainSelected || root.selected
            color: "transparent"
            border.width: root.mainSelected ? 2 : 1.5
            border.color: root.mainSelected ? Colors.sysPalette.highlight : Colors.sysPalette.dark
        }

        // Accepts edges dragged from other nodes' pins:
        // - dropping an output connector creates an edge towards the Dot input
        // - dropping an input connector creates an edge from the Dot output
        DropArea {
            id: dropArea
            // Same negative margins as regular attribute pins to make the connection zone easier to reach
            anchors.fill: parent
            anchors.margins: -2
            keys: [outputDragTarget.objectName]

            property bool acceptableDrop: false

            onEntered: function(drag) {
                // An ongoing drag can be redirected to another Dot (insert Dot while dragging an edge):
                // use the effective source attribute instead of the original connector's one
                var srcAttribute = drag.source.dragRedirectAttribute ? drag.source.dragRedirectAttribute : drag.source.attribute
                if (root.readOnly || drag.source.objectName !== "edgeConnector" || !srcAttribute || srcAttribute.node === node) {
                    // Locked node, not an edge connector, or connection within the same node
                    drag.accepted = false
                } else if (drag.source.connectorType === "output") {
                    // Incoming connection on the Dot input
                    drag.accepted = pin.inputAttribute.validateIncomingConnection(srcAttribute)
                    if (drag.accepted && pin.inputAttribute.isLink) {
                        // The existing edge will be replaced
                        root.edgeAboutToBeRemoved(pin.inputAttribute)
                    }
                } else {
                    // Outgoing connection from the Dot output
                    drag.accepted = pin.outputAttribute.validateIncomingConnection(drag.source.attribute)
                    if (drag.accepted && drag.source.attribute.isLink) {
                        root.edgeAboutToBeRemoved(drag.source.attribute)
                    }
                }
                dropArea.acceptableDrop = drag.accepted
            }

            onExited: function(drag) {
                root.edgeAboutToBeRemoved(undefined)
                dropArea.acceptableDrop = false
                // 'drag' is undefined when the drag ends while still over the DropArea (e.g. right after a drop)
                if (drag && drag.source)
                    drag.source.dropAccepted = false
            }

            onDropped: function(drop) {
                root.edgeAboutToBeRemoved(undefined)
                // An ongoing drag can be redirected to another Dot (insert Dot while dragging an edge)
                var srcAttribute = drop.source.dragRedirectAttribute ? drop.source.dragRedirectAttribute : drop.source.attribute
                if (drop.source.connectorType === "output") {
                    _currentScene.addEdge(srcAttribute, pin.inputAttribute)
                } else {
                    _currentScene.addEdge(pin.outputAttribute, drop.source.attribute)
                }
            }
        }

        // Dragging from the Dot creates an edge from its output attribute
        Item {
            id: outputDragTarget
            objectName: "edgeConnector"
            readonly property string connectorType: "output"
            readonly property alias attribute: pin.outputAttribute
            readonly property alias nodeItem: root
            readonly property bool isOutput: true
            readonly property bool isList: pin.outputAttribute ? pin.outputAttribute.type === "ListAttribute" : false
            readonly property bool isExpandable: pin.outputAttribute ? pin.outputAttribute.isExpandable === true : false
            property bool dropAccepted: false
            /// Whether an edge is currently being dragged from this connector
            readonly property bool dragging: connectMA.drag.active
            /// Attribute to use as the edge source instead of this connector's attribute when set
            /// (an ongoing drag can be redirected to another Dot, see the GraphEditor insert Dot shortcut)
            property var dragRedirectAttribute: null
            width: parent.width
            height: parent.height
            x: parent.width / 2 - width / 2
            y: parent.height / 2 - height / 2
            Drag.keys: [outputDragTarget.objectName]
            Drag.active: connectMA.drag.active
            Drag.hotSpot.x: width * 0.5
            Drag.hotSpot.y: height * 0.5
        }

        // Preview of the edge being created
        Edge {
            id: connectEdge
            // Shown while dragging from the Dot, or while a drag is redirected to it;
            // hidden while this Dot's own drag is redirected to another Dot
            visible: (connectMA.drag.active && !pin.dragRedirected) || (pin.redirectSource !== null && pin.redirectSource.dragging)
            z: 100
            point1x: pin.width / 2
            point1y: pin.height / 2
            point2x: outputDragTarget.x + outputDragTarget.width / 2
            point2y: outputDragTarget.y + outputDragTarget.height / 2
            color: Colors.sysPalette.highlight
            thickness: outputDragTarget.dropAccepted ? 2 : 1
        }

        MouseArea {
            id: connectMA
            anchors.fill: parent
            // Same negative margins as the DropArea, like regular attribute pins
            anchors.margins: -2
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            hoverEnabled: true
            enabled: !root.readOnly
            drag.target: root.readOnly ? undefined : outputDragTarget
            drag.threshold: 0
            drag.smoothed: false
            onPressed: function(mouse) { root.pressed(mouse) }
            onReleased: function(mouse) {
                outputDragTarget.Drag.drop()
                // Clear any drag redirect (insert Dot while dragging an edge)
                outputDragTarget.dragRedirectAttribute = null
                root.released(mouse)
            }
            onClicked: function(mouse) { root.clicked(mouse) }
            onDoubleClicked: function(mouse) { root.doubleClicked(mouse) }
            onEntered: root.entered()
            onExited: root.exited()
            drag.onActiveChanged: {
                if (!drag.active) {
                    // Re-center the drag target once the edge creation is over
                    outputDragTarget.x = pin.width / 2 - outputDragTarget.width / 2
                    outputDragTarget.y = pin.height / 2 - outputDragTarget.height / 2
                }
            }
            cursorShape: drag.active ? Qt.CrossCursor : Qt.PointingHandCursor
        }
    }
}
