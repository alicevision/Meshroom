import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects

import Utils 1.0

import Meshroom.Helpers

/**
 * Visual representation of a Graph Backdrop Node.
 */

Item {
    id: root

    /// The underlying Node object
    property variant node

    /// Mouse related states
    property bool mainSelected: false
    property bool selected: false
    property bool hovered: false

    // The Item instantiating the delegates.
    property Item modelInstantiator: undefined

        // Node Children for the Backdrop
    property var children: []
    
    property bool dragging: mouseArea.drag.active
    property bool resizing: leftDragger.drag.active || topDragger.drag.active
    /// Combined x and y
    property point position: Qt.point(x, y)
    /// Styling
    property color shadowColor: "#cc000000"
    readonly property color defaultColor: node.color === "" ? "#fffb85" : node.color
    property color baseColor: defaultColor

    readonly property int minimumWidth: 200
    readonly property int minumumHeight: 200

    property point mousePosition: Qt.point(mouseArea.mouseX, mouseArea.mouseY)

    // Mouse interaction related signals
    signal pressed(var mouse)
    signal released(var mouse)
    signal clicked(var mouse)
    signal doubleClicked(var mouse)
    signal moved(var position)
    signal entered()
    signal exited()
    
    // Size signal
    signal resized(var width, var height)
    signal resizedAndMoved(var width, var height, var position)

    // Already connected attribute with another edge in DropArea
    signal edgeAboutToBeRemoved(var input)

    /// Emitted when child attribute pins are created
    signal attributePinCreated(var attribute, var pin)
    /// Emitted when child attribute pins are deleted
    signal attributePinDeleted(var attribute, var pin)

    // use node name as object name to simplify debugging
    objectName: node ? node.name : ""

    // initialize position with node coordinates
    x: root.node ? root.node.x : undefined
    y: root.node ? root.node.y : undefined

    // The backdrop node always needs to be at the back
    z: -1

    width: root.node ? root.node.nodeWidth : 300;
    height: root.node ? root.node.nodeHeight : 200;

    implicitHeight: childrenRect.height

    SystemPalette { id: activePalette }

    Connections {
        target: root.node
        // update x,y when node position changes
        function onPositionChanged() {
            root.x = root.node.x
            root.y = root.node.y
        }

        function onInternalAttributesChanged() {
            root.width = root.node.nodeWidth;
            root.height = root.node.nodeHeight;
        }
    }

    // When the node is selected, update the children for it
    // For node to consider another ndoe, it needs to be fully inside the backdrop area
    onSelectedChanged: {
        if (selected) {
            updateChildren()
        }
    }

    function updateChildren() {
        let nodes = [];
        const backdropRect = Qt.rect(root.node.x, root.node.y, root.node.nodeWidth, root.node.nodeHeight);

        for (var i = 0; i < modelInstantiator.count; ++i) {
            const delegate = modelInstantiator.itemAt(i).item;
            if (delegate === this)
                continue

            const delegateRect = Qt.rect(delegate.x, delegate.y, delegate.width, delegate.height);
            if (Geom2D.rectRectFullIntersect(backdropRect, delegateRect)) {
                                nodes.push(delegate);
            }
        }
        children = nodes
    }

    function getChildrenNodes() {
        /**
         * Returns the current nodes which are a part of the Backdrop.
         */
        return children
    }

    // Main Layout
    MouseArea {
        id: mouseArea
        width: root.width;
        height: root.height;
        drag.target: root
        // Small drag threshold to avoid moving the node by mistake
        drag.threshold: 2
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        onPressed: (mouse) => root.pressed(mouse)
        onReleased: (mouse) => root.released(mouse)
        onClicked: (mouse) => root.clicked(mouse)
        onDoubleClicked: (mouse) => root.doubleClicked(mouse)
        onEntered: root.entered()
        onExited: root.exited()
        drag.onActiveChanged: {
            if (!drag.active) {
                root.moved(Qt.point(root.x, root.y))
            }
        }

        cursorShape: drag.active ? Qt.ClosedHandCursor : Qt.ArrowCursor

        /// Backdrop Resize Controls ???
        ///
        /// Resize Right Side
        ///
        Rectangle {
            width: 4
            height: nodeContent.height

            color: baseColor
            opacity: 0

            anchors.horizontalCenter: parent.right

            // This mouse area serves as the dragging rectangle    
            MouseArea {
                id: rightDragger

                cursorShape: Qt.SizeHorCursor
                anchors.fill: parent

                drag { target: parent; axis: Drag.XAxis }

                onMouseXChanged: {
                    if (drag.active) {
                        // Update the area width
                        root.width = root.width + mouseX;

                        // Ensure we have a minimum width always
                        if (root.width < root.minimumWidth) {
                            root.width = root.minimumWidth;
                        }
                    }
                }

                onReleased: {
                    // emit the width and height
                    root.resized(root.width, nodeContent.height);
                }
            }
        }

        ///
        /// Resize Left Side
        ///
        Rectangle {
            width: 4
            height: nodeContent.height

            color: baseColor
            opacity: 0

            anchors.horizontalCenter: parent.left

            // This mouse area serves as the dragging rectangle
            MouseArea {
                id: leftDragger

                cursorShape: Qt.SizeHorCursor
                anchors.fill: parent

                drag { target: parent; axis: Drag.XAxis }

                onMouseXChanged: {
                    if (drag.active) {
                        // Width of the Area
                        let w = 0

                        // Update the area width
                        w = root.width - mouseX

                        // Ensure we have a minimum width always
                        if (w > root.minimumWidth) {
                            // Update the node's x position and the width
                            root.x = root.x + mouseX
                            root.width = w;
                        }
                    }
                }

                onReleased: {
                    // emit the node width and height along with the root position
                    // Dragging from the left moves the node as well
                    root.resizedAndMoved(root.width, root.height, Qt.point(root.x, root.y));
                }
            }
        }

        ///
        /// Resize Bottom
        ///
        Rectangle {
            width: mouseArea.width
            height: 4

            color: baseColor
            opacity: 0

            anchors.verticalCenter: nodeContent.bottom

            MouseArea {
                id: bottomDragger

                cursorShape: Qt.SizeVerCursor
                anchors.fill: parent

                drag{ target: parent; axis: Drag.YAxis }

                onMouseYChanged: {
                    if (drag.active) {
                        // Update the height
                        root.height = root.height + mouseY;

                        // Ensure a minimum height
                        if (root.height < root.minumumHeight) {
                            root.height = root.minumumHeight;
                        }
                    }
                }

                onReleased: {
                    // emit the width and height for it to be updated
                    root.resized(mouseArea.width, root.height);
                }
            }
        }

        ///
        /// Resize Top
        ///
        Rectangle {
            width: mouseArea.width
            height: 4
            
            color: baseColor
            opacity: 0

            anchors.verticalCenter: parent.top

            MouseArea {
                id: topDragger

                cursorShape: Qt.SizeVerCursor
                anchors.fill: parent

                drag{ target: parent; axis: Drag.YAxis }

                onMouseYChanged: {
                    if (drag.active) {
                        let h = root.height - mouseY;

                        // Ensure a minimum height
                        if (h > root.minumumHeight) {
                            // Update the node's y position and the height
                            root.y = root.y + mouseY;
                            root.height = h;
                        }
                    }
                }

                onReleased: {
                    // emit the node width and height along with the root position
                    // Dragging from the top moves the node as well
                    root.resizedAndMoved(root.width, root.height, Qt.point(root.x, root.y));
                }
            }
        }

        // Selection border
        Rectangle {
            anchors.fill: nodeContent
            anchors.margins: -border.width
            visible: root.mainSelected || root.hovered || root.selected
            border.width: {
                if(root.mainSelected)
                    return 3
                if(root.selected)
                    return 2.5
                return 2
            }
            border.color: {
                if(root.mainSelected)
                    return activePalette.highlight
                if(root.selected)
                    return Qt.darker(activePalette.highlight, 1.2)
                return Qt.lighter(activePalette.base, 3)
            }
            opacity: 0.9
            radius: background.radius + border.width
            color: "transparent"
        }

        Rectangle {
            id: background
            anchors.fill: nodeContent
            color: Qt.darker(baseColor, 1.2)
            layer.enabled: true
            layer.effect: DropShadow { radius: 3; color: shadowColor }
            radius: 3
            opacity: 0.7
        }

        Rectangle {
            id: nodeContent
            width: parent.width
            height: parent.height
            color: "transparent"

            // Data Layout
            Column {
                id: body
                width: parent.width

                // Header
                Rectangle {
                    id: header
                    width: parent.width
                    height: headerLayout.height
                    color: root.baseColor
                    radius: background.radius

                    // Fill header's bottom radius
                    Rectangle {
                        width: parent.width
                        height: parent.radius
                        anchors.bottom: parent.bottom
                        color: parent.color
                        z: -1
                    }

                    // Header Layout
                    RowLayout {
                        id: headerLayout
                        width: parent.width
                        spacing: 0

                        // Node Name
                        Label {
                            id: nodeLabel
                            Layout.fillWidth: true
                            text: node ? node.label : ""
                            padding: 4
                            color: "#2b2b2b"
                            elide: Text.ElideMiddle
                            font.pointSize: 8
                        }
                    }
                }

                // Vertical Spacer
                Item { width: parent.width; height: 2 }

                // Node Comments Text which is visible on the backdrop
                Rectangle {
                    y: header.height

                    // Show only when we have a comment
                    visible: node.comment

                    Text {
                        text: node.comment
                        padding: 4
                        font.pointSize: node.fontSize
                    }
                }
            }
        }
    }
}
