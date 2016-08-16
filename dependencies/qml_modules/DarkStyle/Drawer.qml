import QtQuick 2.7
import QtQuick.Templates 2.0 as T

import "."

T.Drawer {

    id: control
    implicitWidth: Math.max(background ? background.implicitWidth : 0, contentWidth + leftPadding + rightPadding)
    implicitHeight: Math.max(background ? background.implicitHeight : 0, contentHeight + topPadding + bottomPadding)
    contentWidth: contentItem.implicitWidth || (contentChildren.length === 1 ? contentChildren[0].implicitWidth : 0)
    contentHeight: contentItem.implicitHeight || (contentChildren.length === 1 ? contentChildren[0].implicitHeight : 0)
    enter: Transition { SmoothedAnimation { velocity: 5 } }
    exit: Transition { SmoothedAnimation { velocity: 5 } }

    contentItem: Item {}
    background: Rectangle {
        color: Globals.window.color.normal
    }
}
