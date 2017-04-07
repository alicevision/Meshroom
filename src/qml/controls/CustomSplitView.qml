import QtQuick 2.5
import QtQuick.Controls 1.4

SplitView {
    id: root
    orientation: Qt.Horizontal
    handleDelegate: Rectangle {
        width: 2
        height: 2
        color: styleData.pressed || styleData.hovered ? "#5BB1F7" : "#101013"

        // avoid cursor shape flickering between split and arrow cursors
        // while resizing the SplitView
        MouseArea {
            id: mouseArea
            anchors.fill: parent
            anchors.margins: styleData.resizing ? -80 : 0
            enabled: false
            cursorShape: root.orientation === Qt.Horizontal ? Qt.SplitHCursor : Qt.SplitVCursor
        }
    }
}
