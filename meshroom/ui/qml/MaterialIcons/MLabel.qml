import QtQuick
import QtQuick.Controls

/**
 * MLabel is a standard Label.
 * If ToolTip.text is set, it shows up a tooltip when hovered.
 */

Label {
    padding: 4
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.NoButton
    }
    ToolTip.visible: mouseArea.containsMouse
    ToolTip.delay: 500
    background: Rectangle {
        anchors.fill: parent
        color: mouseArea.containsMouse ? Qt.darker(parent.palette.base, 0.6) : "transparent"
    }
}
