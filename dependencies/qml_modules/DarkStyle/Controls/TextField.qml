import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import ".."

TextField {

    id: root

    property color color: enabled ? Style.text.color.normal : Style.text.color.disabled
    property color bgcolor: Style.window.color.xdark

    state: ""
    states: [
        State {
            name: "HIDDEN"
            PropertyChanges {
                target: root
                bgcolor: root.activeFocus ? Style.window.color.xdark : "transparent"
            }
        }
    ]

    onAccepted: focus = false
    style: TextFieldStyle {
        textColor: root.color
        placeholderTextColor : Style.text.color.disabled
        font.pixelSize: Style.text.size.normal
        background: Rectangle {
            implicitHeight: 30
            implicitWidth: 200
            color: root.bgcolor
        }
    }
}
