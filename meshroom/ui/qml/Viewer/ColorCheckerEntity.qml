import QtQuick 2.11

Item {
    id: root

    // required for perspective transform
    property real sizeX: 1675.0  // might be overrided in ColorCheckerViewer
    property real sizeY: 1125.0  // might be overrided in ColorCheckerViewer

    property var colors: null

    Rectangle {
        id: canvas
        anchors.centerIn: parent

        width: parent.sizeX
        height: parent.sizeY

        color: "transparent"
        border.width: Math.max(1, (12.0 / zoom))
        border.color: "red"

        transformOrigin: Item.TopLeft
        transform: Matrix4x4 {
            id: transformation
            matrix: Qt.matrix4x4()
        }

    }

    Grid {
        spacing: 12.5
        rows: 4
        columns: 6

        Repeater {
            model: root.colors

            Rectangle {
                width: 125
                height: 125
                color: Qt.rgba(modelData.r, modelData.g, modelData.b, 1.0)
            }
        }
    }


    function transform(matrix) {
        var m = matrix
        transformation.matrix = Qt.matrix4x4(
                m[0][0], m[0][1],  0, m[0][2],
                m[1][0], m[1][1],  0, m[1][2],
                      0,       0,  1,       0,
                m[2][0], m[2][1],  0, m[2][2] )
    }

}
