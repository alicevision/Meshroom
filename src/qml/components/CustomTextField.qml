import QtQuick 2.2
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.2

TextField {
    id: root
    property color color: enabled ? _style.text.color.normal : _style.text.color.disabled
    style: TextFieldStyle {
        textColor: root.color
        placeholderTextColor : _style.text.color.disabled
        font.pointSize: _style.text.size.normal
        background: Rectangle {
            implicitHeight: 30
            implicitWidth: 200
            color: _style.window.color.xdarker
        }
    }
}
