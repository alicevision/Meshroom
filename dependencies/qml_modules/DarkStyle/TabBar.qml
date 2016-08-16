import QtQuick 2.7
import QtQuick.Templates 2.0 as T

import "."

T.TabBar {

    id: control
    implicitWidth: Math.max(background ? background.implicitWidth : 0,
                            contentItem.implicitWidth + leftPadding + rightPadding)
    implicitHeight: Math.max(background ? background.implicitHeight : 0,
                             contentItem.implicitHeight + topPadding + bottomPadding)
    spacing: 1

    contentItem: ListView {
        implicitWidth: contentWidth
        implicitHeight: 30
        model: control.contentModel
        currentIndex: control.currentIndex
        spacing: control.spacing
        orientation: ListView.Horizontal
        boundsBehavior: Flickable.StopAtBounds
        snapMode: ListView.SnapToItem
        highlightMoveDuration: 250
        highlightResizeDuration: 0
        highlightFollowsCurrentItem: true
        highlight: Item {
            z: 2
            Rectangle {
                height: 1
                width: parent.width
                y: control.position === T.TabBar.Footer ? 0 : parent.height - height
                color: Globals.window.color.selected
            }
        }
    }
    background: Item {}
}
