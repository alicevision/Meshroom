import QtQuick
import QtQuick.Controls

import Utils 1.0

/**
 * Visual representation of a conversion node: a small circle in the middle of the edge
 * between the attributes it converts.
 * It can be selected like a node, but cannot be moved: its position follows the connected attributes.
 * It provides the pins of the conversion "input" and "output" attributes, so the edges connected
 * to the conversion node are drawn to the center of the circle.
 */

Item {
    id: root

    /// The conversion node
    property variant node
    /// Pins of the attribute providing the value to convert and of the (first) attribute receiving the converted value
    property var srcPin: null
    property var dstPin: null

    property bool mainSelected: false
    property bool selected: false
    property bool hovered: false
    property bool readOnly: node ? node.locked : false

    readonly property bool isConversionNode: true
    readonly property real radius: 5

    signal pressed(var mouse)
    signal released(var mouse)
    signal clicked(var mouse)
    signal doubleClicked(var mouse)
    signal entered()
    signal exited()

    /// Emitted when the pins of the conversion attributes are created/deleted
    signal attributePinCreated(var attribute, var pin)
    signal attributePinDeleted(var attribute, var pin)

    // Middle of the edge between the connected attributes, or the node position if it is not fully connected
    readonly property point center: {
        if (srcPin && dstPin) {
            return Qt.point((srcPin.globalX + srcPin.outputAnchorPos.x + dstPin.globalX + dstPin.inputAnchorPos.x) / 2,
                            (srcPin.globalY + srcPin.outputAnchorPos.y + dstPin.globalY + dstPin.inputAnchorPos.y) / 2)
        }
        return node ? Qt.point(node.x, node.y) : Qt.point(0, 0)
    }

    x: center.x - radius
    y: center.y - radius
    width: radius * 2
    height: radius * 2

    // Pins used by the edges connected to the conversion node: both are located at the center of the circle
    Item {
        id: inputPin
        readonly property var attribute: root.node ? root.node.inputAttribute : null
        readonly property real globalX: root.x
        readonly property real globalY: root.y
        readonly property point inputAnchorPos: Qt.point(root.radius, root.radius)
        readonly property point outputAnchorPos: Qt.point(root.radius, root.radius)
    }

    Item {
        id: outputPin
        readonly property var attribute: root.node ? root.node.outputAttribute : null
        readonly property real globalX: root.x
        readonly property real globalY: root.y
        readonly property point inputAnchorPos: Qt.point(root.radius, root.radius)
        readonly property point outputAnchorPos: Qt.point(root.radius, root.radius)
    }

    Component.onCompleted: {
        attributePinCreated(inputPin.attribute, inputPin)
        attributePinCreated(outputPin.attribute, outputPin)
    }
    Component.onDestruction: {
        attributePinDeleted(inputPin.attribute, inputPin)
        attributePinDeleted(outputPin.attribute, outputPin)
    }

    Rectangle {
        anchors.centerIn: parent
        width: (root.hovered || root.selected) ? root.radius * 2.6 : root.radius * 2
        height: width
        radius: width / 2
        color: root.selected ? Colors.sysPalette.highlight : Colors.sysPalette.text
        border.color: root.mainSelected ? Colors.sysPalette.highlightedText : Colors.sysPalette.base
        border.width: root.mainSelected ? 2 : 1
    }

    MouseArea {
        id: mouseArea
        // Larger than the circle to ease the selection
        anchors.fill: parent
        anchors.margins: -root.radius
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        cursorShape: Qt.PointingHandCursor

        onPressed: function(mouse) { root.pressed(mouse) }
        onReleased: function(mouse) { root.released(mouse) }
        onClicked: function(mouse) { root.clicked(mouse) }
        onDoubleClicked: function(mouse) { root.doubleClicked(mouse) }
        onEntered: root.entered()
        onExited: root.exited()

        ToolTip {
            visible: mouseArea.containsMouse && !mouseArea.pressed
            delay: 500
            // Beside the circle, so that it never covers it (whatever the zoom level)
            x: mouseArea.width + 2
            y: 0
            text: {
                if (!root.node)
                    return ""
                const label = root.node.label
                const title = "<b>" + label + "</b>" + (label !== root.node.nodeType ? " (" + root.node.nodeType + ")" : "")
                return title + "<br>" + root.node.inputAttribute.value + " → " + root.node.outputAttribute.value
            }
        }
    }
}
