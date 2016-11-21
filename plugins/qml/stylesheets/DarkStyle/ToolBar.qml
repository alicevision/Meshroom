import QtQuick 2.6
import QtQuick.Templates 2.0 as T

import "."

T.ToolBar {

    id: control
    implicitWidth: Math.max(background ? background.implicitWidth : 0, contentWidth + leftPadding + rightPadding)
    implicitHeight: Math.max(background ? background.implicitHeight : 0, contentHeight + topPadding + bottomPadding)
    contentWidth: contentItem.implicitWidth || (contentChildren.length === 1 ? contentChildren[0].implicitWidth : 0)
    contentHeight: contentItem.implicitHeight || (contentChildren.length === 1 ? contentChildren[0].implicitHeight : 0)

    contentItem: Item {}
    background: Rectangle {
        implicitHeight: 30
        color: Globals.window.color.xdark
    }
}
