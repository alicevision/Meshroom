import QtQuick 2.7
import QtQuick.Templates 2.0 as T

import "."

T.ToolButton {

    id: control
    property url icon: ""

    implicitWidth: 30
    implicitHeight: 30
    text: qsTr("ToolButton")
    hoverEnabled: true
    padding: 2

    contentItem: Rectangle {
        color: "transparent"
        border.color: control.enabled ? Globals.window.color.xlight : Globals.window.color.disabled
        visible: control.icon == ""
    }
    background: Rectangle {
        color: control.hovered ? Globals.window.color.selected : "transparent"
        opacity: 0.8
        Behavior on color { ColorAnimation {} }
        Image {
            anchors.fill: parent
            visible: control.icon != ""
            source: control.icon
            sourceSize: Qt.size(40, 40)
            asynchronous: true
        }
    }

}
