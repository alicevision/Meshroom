import QtQuick 2.7
import QtQuick.Templates 2.0 as T

import "."

T.ToolButton {

    id: control
    implicitWidth: 30
    implicitHeight: 30
    text: qsTr("ToolButton")
    hoverEnabled: true
    padding: 2

    contentItem: Rectangle {
        color: "transparent"
        border.color: control.enabled ? Globals.window.color.xlight : Globals.window.color.disabled
    }
    background: Rectangle {
        color: control.hovered ? Globals.window.color.selected : Globals.window.color.dark
        opacity: 0.8
        Behavior on color { ColorAnimation {} }
    }

}
