import QtQuick
import QtQuick.Controls

/**
 * MaterialLabel is a standard Label using MaterialIcons font.
 * If ToolTip.text is set, it also shows up a tooltip when hovered.
 */

Label {
    font.family: MaterialIcons.fontFamily
    font.pointSize: 10
    ToolTip.visible: toolTipLoader.active && toolTipLoader.item.containsMouse
    ToolTip.delay: 1000

    Loader {
        id: toolTipLoader
        anchors.fill: parent
        active: parent.ToolTip.text
        sourceComponent: MouseArea {
            hoverEnabled: true
            acceptedButtons: Qt.NoButton
        }
    }
}
