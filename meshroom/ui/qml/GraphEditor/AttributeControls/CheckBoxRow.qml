import QtQuick
import QtQuick.Controls

Row {
    id: root
    property bool editable
    property var keyedValue
    signal toggled()
    CheckBox {
        enabled: root.editable
        checked: root.keyedValue
        onToggled: {
            root.toggled()
        }
    }
}