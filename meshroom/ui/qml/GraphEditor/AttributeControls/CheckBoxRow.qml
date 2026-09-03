import QtQuick
import QtQuick.Controls

Item {
    id: root
    property bool editable
    property var checked
    signal toggled()
    implicitWidth: innerCheckBox.implicitWidth
    implicitHeight: innerCheckBox.implicitHeight
    CheckBox {
        id: innerCheckBox
        anchors.fill: parent
        enabled: root.editable
        checked: root.checked
        onToggled: {
            root.toggled()
        }
    }
    Rectangle {
        anchors.fill: innerCheckBox
        color: "transparent"
        radius: 2
        border.width: innerCheckBox.activeFocus 
                      ? 2
                      : 0
        border.color: root.palette.highlight
        z: 10
        enabled: false
    }
}