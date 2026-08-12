import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

RowLayout {
    id: root
    required property var value
    property bool editable
    property string previousColor: ""
    signal clicked(var checked, var previousColor, var colorTextValue)
    signal editingFinished(var text)
    signal accepted(var text)
    signal destruction(bool activeFocus, var text)
    CheckBox {
        id: colorCheckbox
        Layout.alignment: Qt.AlignLeft
        checked: root.value === "" ? false : true
        checkable: root.editable
        text: "Custom Color"
        onClicked: {
            root.clicked(checked, previousColor, colorText.text)

        }
    }
    TextField {
        id: colorText
        Layout.alignment: Qt.AlignLeft
        implicitWidth: 100
        enabled: colorCheckbox.checked && root.editable
        visible: colorCheckbox.checked
        text: colorCheckbox.checked ? root.value : ""
        selectByMouse: true
        onEditingFinished: root.editingFinished( text)
        onAccepted: root.accepted(text)
        Component.onDestruction: root.destruction(activeFocus, text)
    }
    Rectangle {
        height: colorText.height
        width: colorText.width / 2
        Layout.alignment: Qt.AlignLeft
        visible: colorCheckbox.checked
        color: colorCheckbox.checked ? colorDialog.selectedColor : ""
        MouseArea {
            enabled: root.editable
            anchors.fill: parent
            onClicked: colorDialog.open()
        }
    }
    ColorDialog {
        id: colorDialog
        title: "Please choose a color"
        selectedColor: colorText.text
        onAccepted: {
            colorText.text = colorDialog.selectedColor
            // Artificially trigger change of value
            colorText.editingFinished()
            close()
        }
        onRejected: close()
    }
    Item {
        // Dummy item to fill out the space if needed
        Layout.fillWidth: true
    }
}