import QtQuick 2.6
import QtQuick.Templates 2.0 as T

import "."

T.ToolBar {

    id: control
    implicitWidth: Math.max(background ? background.implicitWidth : 0, contentWidth + leftPadding + rightPadding)
    implicitHeight: Math.max(background ? background.implicitHeight : 0, contentHeight + topPadding + bottomPadding)

    contentItem: Item {}
    background: Rectangle {
        implicitHeight: 40
        color: Globals.window.color.xdark
        Rectangle {
            height: 1
            width: parent.width
            anchors.bottom: parent.bottom
            color: Qt.darker(Globals.window.color.xdark, 1.5)
        }
    }
}
