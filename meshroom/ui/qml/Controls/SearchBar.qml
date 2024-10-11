import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import MaterialIcons 2.2

/**
 * Basic SearchBar component with an appropriate icon and a TextField.
 */

FocusScope {
    property alias textField: field
    property alias text: field.text

    implicitHeight: childrenRect.height
    Keys.forwardTo: [field]

    function forceActiveFocus() {
        field.forceActiveFocus()
    }

    function clear() {
        field.clear()
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

            // Ensure the field has focus when the text is modified
            onTextChanged: {
                forceActiveFocus()
            }
        }
    }
}


