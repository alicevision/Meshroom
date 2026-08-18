import QtQuick
import QtQuick.Controls

Row {
    id: root
    property bool editable
    property var checked
    signal toggled()
    CheckBox {
        enabled: root.editable
        checked: root.checked
        onToggled: {
            root.toggled()
        }
    }
}