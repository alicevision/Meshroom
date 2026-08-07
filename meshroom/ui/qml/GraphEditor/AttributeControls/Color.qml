import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

RowLayout {
    id: root
    required property var attribute
    property bool editable
    CheckBox {
        id: colorCheckbox
        Layout.alignment: Qt.AlignLeft
        checked: attribute.value === "" ? false : true
        checkable: root.editable
        text: "Custom Color"
        property string previousColor: ""
        onClicked: {
            if (checked) {
                if (colorText.text == "") {
                    if (previousColor != "")
                        _currentScene.setAttribute(attribute, previousColor)
                    else
                        _currentScene.setAttribute(attribute, "#0000FF")
                }
                else
                    _currentScene.setAttribute(attribute, colorText.text)
            } else {
                previousColor = attribute.value
                _currentScene.setAttribute(attribute, "")
            }
        }
    }
    TextField {
        id: colorText
        Layout.alignment: Qt.AlignLeft
        implicitWidth: 100
        enabled: colorCheckbox.checked && root.editable
        visible: colorCheckbox.checked
        text: colorCheckbox.checked ? attribute.value : ""
        selectByMouse: true
        onEditingFinished: setTextFieldAttribute(root.attribute, text)
        onAccepted: setTextFieldAttribute(root.attribute, text)
        Component.onDestruction: {
            if (activeFocus)
                setTextFieldAttribute(root.attribute, text)
        }
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
            // Artificially trigger change of attribute value
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