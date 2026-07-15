import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Shapes 1.6

import GraphEditor 1.0
import MaterialIcons 2.2
import Utils 1.0

/**
 * A cubic spline representing an edge, going from point1 to point2, providing mouse interaction.
 */

Item {
    id: root

    property var edge
    property real point1x
    property real point1y
    property real point2x
    property real point2y
    property alias thickness: path.strokeWidth
    property alias color: path.strokeColor
    property bool isForLoop: false
    property int loopSize: 0
    property int iteration: 0

    readonly property bool hasConverter: edge !== undefined && edge !== null && edge.hasConverter === true

    // Note: edgeArea is destroyed before path, so we need to test if not null to avoid warnings.
    readonly property bool containsMouse: (loopArea && loopArea.containsMouse) || (edgeArea && edgeArea.containsMouse)

    signal pressed(var event)
    signal released(var event)

    x: point1x
    y: point1y
    width: point2x - point1x
    height: point2y - point1y

    property real startX: 0
    property real startY: 0
    property real endX: width
    property real endY: height


    function intersectsSegment(p1, p2) {
        /**
         * Detects whether a line along the given rects diagonal intersects with the edge mouse area.
         */
        // The edgeArea is within the parent Item and its bounds and position are relative to its parent
        // Map the original rect to the coordinates of the edgeArea by subtracting the parent's coordinates from the rect
        // This mapped rect would ensure that the rect coordinates map to 0 of the edge area
        return edgeArea.intersectsSegment(Qt.point(p1.x - x, p1.y - y), Qt.point(p2.x - x, p2.y - y));
    }

    Shape {
        anchors.fill: parent
        // Cause rendering artifacts when enabled (and do not support hot reload really well)
        vendorExtensionsEnabled: false
        opacity: 0.7

        ShapePath {
            id: path
            startX: root.startX
            startY: root.startY
            fillColor: "transparent"

            strokeColor: "#3E3E3E"
            strokeStyle: edge !== undefined && ((edge.src !== undefined && edge.src.isOutput) || edge.dst === undefined) ? ShapePath.SolidLine : ShapePath.DashLine
            strokeWidth: 1
            // Final visual width of this path (never below 1)
            readonly property real visualWidth: Math.max(strokeWidth, 1)
            dashPattern: [6 / visualWidth, 4 / visualWidth]
            capStyle: ShapePath.RoundCap

            PathCubic {
                id: cubic
                property real ctrlPtDist: 30
                x: root.isForLoop ? (root.startX + root.endX) / 2  - loopArea.width / 2 : root.endX
                y: root.isForLoop ? (root.startY + root.endY) / 2 : root.endY
                relativeControl1X: ctrlPtDist
                relativeControl1Y: 0
                control2X: x - ctrlPtDist
                control2Y: y
            }
        }

        ShapePath {
            id: pathSecondary
            startX: (root.startX + root.endX) / 2 + loopArea.width / 2
            startY: (root.startY + root.endY) / 2
            fillColor: "transparent"

            strokeColor: root.isForLoop ? root.color : "transparent"
            strokeStyle: edge !== undefined && ((edge.src !== undefined && edge.src.isOutput) || edge.dst === undefined) ? ShapePath.SolidLine : ShapePath.DashLine
            strokeWidth: root.thickness
            // Final visual width of this path (never below 1)
            readonly property real visualWidth: Math.max(strokeWidth, 1)
            dashPattern: [6 / visualWidth, 4 / visualWidth]
            capStyle: ShapePath.RoundCap

            PathCubic {
                id: cubicSecondary
                property real ctrlPtDist: 30
                x: root.endX
                y: root.endY
                relativeControl1X: ctrlPtDist
                relativeControl1Y: 0
                control2X: x - ctrlPtDist
                control2Y: y
            }
        }
    }

    Item {
        // Place the label at the middle of the edge
        x: (root.startX + root.endX) / 2
        y: (root.startY + root.endY) / 2
        z: 1
        visible: root.isForLoop || root.hasConverter

        RowLayout {
            anchors.centerIn: parent
            spacing: 4

            // For-loop badge
            Rectangle {
                visible: root.isForLoop
                property int margin: 2
                Layout.preferredWidth: icon.width + 2 * margin
                Layout.preferredHeight: icon.height + 2 * margin
                radius: width
                color: path.strokeColor

                MaterialToolLabel {
                    id: icon
                    anchors.centerIn: parent

                    iconText: MaterialIcons.loop
                    label.text: (root.iteration + 1) + "/" + root.loopSize + " "

                    labelIconColor: palette.base
                    ToolTip.text: "Foreach Loop"
                }

                MouseArea {
                    id: loopArea
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: root.pressed(arguments[0])
                }
            }

            // Converter badge
            Rectangle {
                id: converterBadge
                visible: root.hasConverter
                property int margin: 2
                Layout.preferredWidth: 10
                Layout.preferredHeight: 10
                radius: width
                color: Colors.lightpurple
                border.color: "#aaa"
                border.width: 0.5

                MouseArea {
                    id: converterArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    acceptedButtons: Qt.RightButton
                    onClicked: (mouse) => converterMenu.popup()
                }

                ToolTip {
                    visible: converterArea.containsMouse
                    delay: 400
                    text: root.edge ? qsTr(root.edge.converterDescription) : ""
                    x: converterBadge.width + 4
                    y: converterBadge.height - height / 2
                }
            }
        }
    }

    EdgeMouseArea {
        id: edgeArea
        z: 0
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        thickness: root.thickness + 4
        curveScale: cubic.ctrlPtDist / root.width  // Normalize by width
        onPressed: function(event) {
            root.pressed(event)
        }
        onReleased: function(event) {
            root.released(event)
        }

    }

    Menu {
        id: converterMenu
        title: "Convert Attribute"

        ButtonGroup {
            id: converterChoices
        }

        Instantiator {
            model: root.edge ? root.edge.availableConverters : []
            RadioButton {
                text: modelData.name
                ButtonGroup.group: converterChoices
                checked: root.edge && root.edge.converterName === modelData.name
                onToggled: {
                    if (checked) root.edge.setConverter(modelData.name)
                    converterMenu.close()
                }
            }
            onObjectAdded: (index, object) => converterMenu.insertItem(index, object)
            onObjectRemoved: (index, object) => converterMenu.removeItem(object)
        }
    }
}
