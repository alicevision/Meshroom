import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import MaterialIcons 2.2

/**
 * Basic SearchBar component with an appropriate icon and a TextField.
 */

FocusScope {
    id: root
    property alias textField: field
    property alias text: field.text

    // Enables hiding and showing of the text field on Search button click
    property bool toggle: false
    property bool isVisible: false

    // Size properties
    property int maxWidth: 150
    property int minWidth: 30

    // The default width is computed based on whether toggling is enabled and if the visibility is true
    width: toggle && isVisible ? maxWidth : minWidth

    // Keyboard interaction related signals
    signal accepted()

    implicitHeight: childrenRect.height
    Keys.forwardTo: [field]

    function forceActiveFocus() {
        field.forceActiveFocus()
    }

    function clear() {
        field.clear()
    }

    RowLayout {
        spacing: 0
        width: parent.width

        MaterialToolButton {
            text: MaterialIcons.search

            onClicked: {
                isVisible = !root.isVisible
                // Set Focus on the Text Field
                field.focus = field.visible
            }
        }

        TextField {
            id: field
            focus: true
            Layout.fillWidth: true
            selectByMouse: true

            rightPadding: clear.width

            // The text field is visible either when toggle is not activated or the visible property is set
            visible: root.toggle ? root.isVisible : true

            // Ensure the field has focus when the text is modified
            onTextChanged: {
                forceActiveFocus()
            }

            // Handle enter Key press and forward it to the parent
            Keys.onPressed: (event)=> {
                if ((event.key == Qt.Key_Return || event.key == Qt.Key_Enter)) {
                    event.accepted = true
                    root.accepted()
                }
            }

            MaterialToolButton {
                id: clear

                // Anchors
                anchors.right: parent.right
                anchors.rightMargin: 2  // Leave a tiny bit of space so that its highlight does not overlap with the boundary of the parent
                anchors.verticalCenter: parent.verticalCenter

                // Style
                font.pointSize: 8
                text: MaterialIcons.close
                ToolTip.text: "Clears text."

                // States
                visible: field.text

                // Signals -> Slots
                onClicked: {
                    field.text = ""
                    parent.focus = true
                }
            }
        }
    }
}


