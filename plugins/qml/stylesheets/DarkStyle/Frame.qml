import QtQuick 2.7
import QtQuick.Templates 2.0 as T

import "."

T.Frame {

    id: control

    contentWidth: contentItem.implicitWidth || (contentChildren.length === 1 ? contentChildren[0].implicitWidth : 0)
    contentHeight: contentItem.implicitHeight || (contentChildren.length === 1 ? contentChildren[0].implicitHeight : 0)
    contentItem: Item {}
    background: Item {}

    Rectangle {
        anchors.top: parent.top
        anchors.right: parent.right
        height: parent.height
        width: 1
        visible: control.activeFocus
        color: Globals.window.color.normal
        z: 100
    }
}
