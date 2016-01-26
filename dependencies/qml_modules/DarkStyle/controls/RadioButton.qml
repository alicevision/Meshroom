import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.2
import ".."
import "."

RadioButton {

    id: root
    text: "radio"
    style: RadioButtonStyle {
        indicator: Rectangle {
                implicitWidth: 16
                implicitHeight: 16
                radius: 9
                color: Style.window.color.xdark
                border.color: (control.hovered && !control.checked) ? Style.window.color.selected : Style.window.color.normal
                border.width: 1
                Rectangle {
                    anchors.fill: parent
                    visible: control.checked
                    color: Style.window.color.selected
                    radius: 9
                    anchors.margins: 2
                }
        }
        label: Text {
            text: control.text
            font.pixelSize: Style.text.size.small
            color: control.hovered ? Style.text.color.light : Style.text.color.normal
        }
    }

 }
