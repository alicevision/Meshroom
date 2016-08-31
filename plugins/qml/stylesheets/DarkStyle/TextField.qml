import QtQuick 2.7
import QtQuick.Templates 2.0 as T

import "."

T.TextField {

    id: control
    implicitWidth: 200
    implicitHeight: 30
    text: qsTr("TextField")
    color: Globals.text.color.normal
    selectionColor: Globals.window.color.dark
    selectedTextColor: Globals.text.color.selected
    verticalAlignment: TextInput.AlignVCenter

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
    background: Rectangle {
        y: control.height - height - control.bottomPadding / 2
        implicitWidth: 120
        height: control.activeFocus ? 2 : 1
        color: Globals.window.color.selected
    }

}
