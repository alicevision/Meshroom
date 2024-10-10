import QtQuick
import QtQuick.Controls

/**
 * A custom CheckBox designed to be used in ChartView's legend.
 */

CheckBox {
    id: root

    property color color

    leftPadding: 0
    font.pointSize: 8

    indicator: Rectangle {
        width: 11
        height: width
        border.width: 1
        border.color: root.color
        color: "transparent"
        anchors.verticalCenter: parent.verticalCenter

        Rectangle {
            anchors.fill: parent
            anchors.margins: parent.border.width + 1
            visible: parent.parent.checkState != Qt.Unchecked
            anchors.topMargin: parent.parent.checkState === Qt.PartiallyChecked ? 5 : 2
            anchors.bottomMargin: anchors.topMargin
            color: parent.border.color
            anchors.centerIn: parent
        }
    }
}
