import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

TextField {
    id: root
    property color color: enabled ? _style.text.color.normal : _style.text.color.disabled
    property color bgcolor: _style.window.color.xdarker
    property int textSize: _style.text.size.normal

    state: ""
    states: [
        State {
            name: "HIDDEN"
            PropertyChanges {
                target: root
                bgcolor: root.activeFocus? _style.window.color.xdarker : "transparent"
            }
        }
    ]

    style: TextFieldStyle {
        textColor: root.color
        placeholderTextColor : _style.text.color.disabled
        font.pixelSize: root.textSize
        background: Rectangle {
            implicitHeight: 30
            implicitWidth: 200
            color: root.bgcolor
        }
    }
}
