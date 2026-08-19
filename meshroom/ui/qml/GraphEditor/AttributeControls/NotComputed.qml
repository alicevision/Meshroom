import QtQuick
import MaterialIcons

MaterialLabel {
    anchors.fill: parent
    text: MaterialIcons.do_not_disturb_alt
    horizontalAlignment: Text.AlignHCenter
    verticalAlignment: Text.AlignVCenter
    padding: 4
    background: Rectangle {
        anchors.fill: parent
        border.width: 0
        radius: 20
        color: Qt.darker(palette.window, 1.1)
    }
}