import QtQuick 2.9
import GraphEditor 1.0
import QtQuick.Shapes 1.0

/**
    A cubic spline representing an edge, going from point1 to point2, providing mouse interaction.
*/
Shape {
    id: root

    property var edge
    property real point1x
    property real point1y
    property real point2x
    property real point2y
    property alias thickness: path.strokeWidth
    property alias color: path.strokeColor

    // BUG: edgeArea is destroyed before path, need to test if not null to avoid warnings
    readonly property bool containsMouse: edgeArea && edgeArea.containsMouse

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

    // cause rendering artifacts when enabled (and don't support hot reload really well)
    vendorExtensionsEnabled: false

    ShapePath {
        id: path
        startX: root.startX
        startY: root.startY
        fillColor: "transparent"
        strokeColor: "#3E3E3E"
        strokeStyle: edge != undefined && ((edge.src != undefined && edge.src.isOutput) || edge.dst == undefined) ? ShapePath.SolidLine : ShapePath.DashLine
        strokeWidth: 1
        // final visual width of this path (never below 1)
        readonly property real visualWidth: Math.max(strokeWidth, 1)
        dashPattern: [6/visualWidth, 4/visualWidth]
        capStyle: ShapePath.RoundCap

        PathCubic {
            id: cubic
            property real ctrlPtDist: 30
            x: root.endX
            y: root.endY
            relativeControl1X: ctrlPtDist; relativeControl1Y: 0
            control2X: x - ctrlPtDist; control2Y: y
        }
    }

    EdgeMouseArea {
        id: edgeArea
        anchors.fill: parent
        curveScale: cubic.ctrlPtDist / root.width  // normalize by width
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        thickness: root.thickness + 4
        onPressed: root.pressed(arguments[0])   // can't get named args, use arguments array
        onReleased: root.released(arguments[0])
    }
}
