import QtQuick 2.9
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import MaterialIcons 2.2


/**
 * Basic SearchBar component with an appropriate icon and a TextField.
 */
FocusScope {
    id: root

    property alias textField: field
    property alias text: field.text
    property bool fixFocus: false

    implicitHeight: childrenRect.height
    Keys.forwardTo: [field]

    function forceActiveFocus() {
        field.forceActiveFocus()
    }

    function clear() {
        field.clear()
    }

    onActiveFocusChanged: {
        if ((fixFocus) && (!activeFocus) && (field.hovered)) {
            field.forceActiveFocus()
        }
    }

    RowLayout {
        width: parent.width

        MaterialLabel {
            text: MaterialIcons.search
        }

        TextField {
            id: field
            focus: true
            Layout.fillWidth: true
            selectByMouse: true

            Keys.onPressed: {
                if ((root.fixFocus) && (text != "")) {
                    forceActiveFocus()
                }
            }
        }
    }
}


