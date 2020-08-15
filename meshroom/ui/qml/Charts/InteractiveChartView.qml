import QtQuick 2.9
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import MaterialIcons 2.2
import QtPositioning 5.8
import QtLocation 5.9

import QtCharts 2.13

import Controls 1.0
import Utils 1.0


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

            property double degreeToScale: 1.0 / 120.0 // default mouse scroll is 15 degree
            acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
            // onWheel: {
            //     console.warn("root.plotArea before: " + root.plotArea)
            //     var zoomFactor = wheel.angleDelta.y > 0 ? 1.0 / (1.0 + wheel.angleDelta.y * degreeToScale) : (1.0 + Math.abs(wheel.angleDelta.y) * degreeToScale)

            //     // var mouse_screen = Qt.point(wheel.x, wheel.y)
            //     var mouse_screen = mapToItem(root, wheel.x, wheel.y)
            //     var mouse_normalized = Qt.point(mouse_screen.x / plotZone.width, mouse_screen.y / plotZone.height)
            //     var mouse_plot = Qt.point(mouse_normalized.x * plotZone.width, mouse_normalized.y * plotZone.height)

            //     // var p = mapToValue(mouse_screen, root.series(0))
            //     // var pMin = mapToValue(mouse_screen, Qt.point(root.axisX().min, root.axisY().min))
            //     // var pMax = mapToValue(mouse_screen, Qt.point(root.axisX().max, root.axisY().max))
            //     // console.warn("p: " + p)

            //     // Qt.rect()
            //     var r = Qt.rect(mouse_plot.x, mouse_plot.y, plotZone.width * zoomFactor, plotZone.height * zoomFactor)
            //     //var r = Qt.rect(pMin.x, pMin.y, (pMax.x-pMin.x) / 2, (pMax.y-pMin.y) / 2)
            //     root.zoomIn(r)
            // }
            onClicked: {
                    root.zoomReset();
            }
        }
    }


}
