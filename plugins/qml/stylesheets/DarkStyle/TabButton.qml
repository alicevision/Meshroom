import QtQuick 2.7
import QtQuick.Templates 2.0 as T

import "."

T.TabButton {

    id: control
    implicitWidth: Math.max(background ? background.implicitWidth : 0,
                            contentItem.contentWidth + leftPadding + rightPadding)
    implicitHeight: Math.max(background ? background.implicitHeight : 0,
                             contentItem.contentHeight + topPadding + bottomPadding)
    baselineOffset: contentItem.y + contentItem.baselineOffset
    padding: 6

    contentItem: Text {
        text: control.text
        font: control.font
        elide: Text.ElideRight
        color: !control.enabled ? Globals.text.color.disabled : control.down || control.checked ? Globals.text.color.selected : Globals.text.color.normal
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }
    background: Item {
        implicitHeight: 30
    }

}
