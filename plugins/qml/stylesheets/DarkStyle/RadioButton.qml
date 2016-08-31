import QtQuick 2.7
import QtQuick.Templates 2.0 as T

import "."

T.RadioButton {

    id: control
    implicitWidth: contentItem.implicitWidth + leftPadding + rightPadding
    implicitHeight: 30
    text: qsTr("RadioButton")
    spacing: 10
    padding: 2

    indicator: Rectangle {
        implicitWidth: 15
        implicitHeight: 15
        x: control.leftPadding
        y: parent.height / 2 - height / 2
        color: Globals.window.color.dark
        radius: 15
        Rectangle {
            anchors.fill: parent
            anchors.margins: 2
            radius: 15
            color: Globals.window.color.selected
            visible: control.checked
        }
    }
    contentItem: Text {
        text: control.text
        font: control.font
        opacity: enabled ? 1.0 : 0.3
        color: Globals.text.color.normal
        verticalAlignment: Text.AlignVCenter
        leftPadding: control.indicator.width + control.spacing
    }

}
