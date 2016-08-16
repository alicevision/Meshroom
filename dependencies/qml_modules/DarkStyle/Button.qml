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
        color: control.enabled ? Globals.text.color.normal : Globals.text.color.disabled
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
    background: Rectangle {
        color: control.hovered ? Globals.window.color.selected : Globals.window.color.dark
        opacity: 0.8
        Behavior on color { ColorAnimation {} }
    }

}
