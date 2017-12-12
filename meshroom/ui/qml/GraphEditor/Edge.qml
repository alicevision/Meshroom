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
        capStyle: ShapePath.RoundCap
        strokeWidth: 1

        PathCubic {
            id: cubic
            property real curveScale: 0.7
            property real ctrlPtDist: Math.abs(root.width * curveScale)
            x: root.endX
            y: root.endY
            relativeControl1X: ctrlPtDist; relativeControl1Y: 0
            control2X: x - ctrlPtDist; control2Y: y
        }
    }

    EdgeMouseArea {
        id: edgeArea
        anchors.fill: parent
        curveScale: cubic.curveScale
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        thickness: root.thickness + 2
        onPressed: root.pressed(arguments[0])   // can't get named args, use arguments array
        onReleased: root.released(arguments[0])
    }
}
