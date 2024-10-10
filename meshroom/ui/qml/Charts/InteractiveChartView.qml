import QtQuick
import QtQuick.Layouts
import QtCharts

ChartView {
    id: root
    antialiasing: true

    Rectangle {
        id: plotZone
        x: root.plotArea.x
        y: root.plotArea.y
        width: root.plotArea.width
        height: root.plotArea.height
        color: "transparent"

        MouseArea {
            anchors.fill: parent

            property double degreeToScale: 1.0 / 120.0 // Default mouse scroll is 15 degree
            acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
            onClicked: {
                root.zoomReset()
            }
        }
    }
}
