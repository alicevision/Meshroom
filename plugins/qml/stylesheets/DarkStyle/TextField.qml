import QtQuick 2.7
import QtQuick.Templates 2.0 as T

import "."

T.TextField {

    id: control
    implicitWidth: 200
    implicitHeight: 30
    color: Globals.text.color.normal
    selectionColor: Globals.window.color.dark
    selectedTextColor: Globals.text.color.selected
    verticalAlignment: TextInput.AlignVCenter
    leftPadding: 4
    rightPadding: 4
    selectByMouse: true

    Text {
        id: placeholder
        x: control.leftPadding
        y: control.topPadding
        width: control.width - (control.leftPadding + control.rightPadding)
        height: control.height - (control.topPadding + control.bottomPadding)
        text: control.placeholderText
        font: control.font
        color: Globals.text.color.dark
        horizontalAlignment: control.horizontalAlignment
        verticalAlignment: control.verticalAlignment
        elide: Text.ElideRight
        visible: !control.length && !control.preeditText && (!control.activeFocus || control.horizontalAlignment !== Qt.AlignHCenter)
    }
    background: Item {
        implicitWidth: 120
        Rectangle {
            anchors.fill: parent
            color: "black"
            opacity: 0.3
        }
        Rectangle {
            y: control.height - height - control.bottomPadding / 2
            height: control.activeFocus ? 2 : 1
            width: parent.width
            color: Globals.window.color.selected
        }
    }

}
