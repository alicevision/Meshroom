import QtQuick 2.7
import QtQuick.Templates 2.0 as T

import "."

T.Button {

    id: control
    implicitWidth: contentItem.implicitWidth + leftPadding + rightPadding
    implicitHeight: 30
    text: qsTr("Button")
    hoverEnabled: true
    padding: 10

    contentItem: Text {
        text: control.text
        font.pixelSize: Globals.text.size.small
        font.family: control.font.family
        color: control.enabled ? Globals.text.color.normal : Globals.text.color.disabled
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideMiddle
    }
    background: Item {
        implicitWidth: 120
        Rectangle {
            y: control.height - height - control.bottomPadding / 2
            height: 1
            width: parent.width
            color: Globals.window.color.selected
            opacity: control.hovered ? 1 : 0
            Behavior on opacity { NumberAnimation {} }
        }
    }
}
