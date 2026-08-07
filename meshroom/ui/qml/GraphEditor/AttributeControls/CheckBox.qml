import QtQuick
import QtQuick.Controls

Row {
    id: root
    property bool editable
    property bool keyable
    property var keyedValue
    property var plainValue
    signal wasFired()
    CheckBox {
        enabled: root.editable
        checked: root.keyable 
                 ? root.keyedValue
                 : root.plainValue
        onToggled: {
            root.wasFired()
        }
    }
}