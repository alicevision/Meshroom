import QtQuick
import QtQuick.Layouts
import QtQuick.Controls

RowLayout {
    id: root

    Layout.fillWidth: true

    property variant attribute: null
    property int rowIndex: model.row
    property int columnIndex: model.column
    property bool readOnly: false
    property string toolTipText: {
        if (!attribute || Object.keys(attribute).length === 0)
            return ""
        return attribute.fullLabel
    }

    Pane {
        Layout.minimumWidth: loaderComponent.width
        Layout.minimumHeight: loaderComponent.height
        Layout.fillWidth: true

        padding: 0

        hoverEnabled: true

        // Tooltip to replace headers for now (header incompatible atm)
        ToolTip.delay: 10
        ToolTip.timeout: 5000
        ToolTip.visible: hovered
        ToolTip.text: toolTipText

        Rectangle {
            width: parent.width
            height: loaderComponent.height

            color: rowIndex % 2 ? palette.window : Qt.darker(palette.window, 1.1)
            border.width: 2
            border.color: Qt.darker(palette.window, 1.2)
            clip: true
            Loader {
                id: loaderComponent
                active: !!attribute // convert to bool with "!!"
                sourceComponent: {
                    if (!attribute)
                        return undefined
                    switch (attribute.type) {
                       case "ChoiceParam": return choiceComponent
                       case "IntParam": return intComponent
                       case "FloatParam": return floatComponent
                       case "BoolParam": return boolComponent
                       case "StringParam": return textFieldComponent
                       case "File": return textFieldComponent
                       default: return undefined
                    }
                }
            }
        }
    }

    Component {
        id: textFieldComponent
        TextInput {
            text: attribute.value
            width: intrinsicModel.columnWidths[columnIndex]
            horizontalAlignment: TextInput.AlignRight
            readOnly: root.readOnly
            color: palette.text

            padding: 12

            selectByMouse: true
            selectionColor: palette.text
            selectedTextColor: Qt.darker(palette.window, 1.1)

            onEditingFinished: _reconstruction.setAttribute(attribute, text)
            onAccepted: {
                _reconstruction.setAttribute(attribute, text)
            }
            Component.onDestruction: {
                if (activeFocus)
                    _reconstruction.setAttribute(attribute, text)
            }
        }
    }

    Component {
        id: intComponent

        TextInput {
            text: model.display.value
            width: intrinsicModel.columnWidths[columnIndex]
            horizontalAlignment: TextInput.AlignRight
            color: palette.text
            readOnly: root.readOnly

            padding: 12

            selectByMouse: true
            selectionColor: palette.text
            selectedTextColor: Qt.darker(palette.window, 1.1)

            IntValidator {
                id: intValidator
            }

            validator: intValidator

            onEditingFinished: _reconstruction.setAttribute(attribute, Number(text))
            onAccepted: {
                _reconstruction.setAttribute(attribute, Number(text))
            }
            Component.onDestruction: {
                if (activeFocus)
                    _reconstruction.setAttribute(attribute, Number(text))
            }
        }
    }

    Component {
        id: choiceComponent
        ComboBox {
            id: combo
            model: attribute.desc !== undefined ? attribute.desc.values : undefined
            width: intrinsicModel.columnWidths[columnIndex]
            enabled: !root.readOnly

            flat : true

            topInset: 7
            leftInset: 6
            rightInset: 6
            bottomInset: 7

            Component.onCompleted: currentIndex = find(attribute.value)
            onActivated: _reconstruction.setAttribute(attribute, currentText)

            Connections {
                target: attribute
                function onValueChanged() { combo.currentIndex = combo.find(attribute.value) }
            }
        }
    }

    Component {
        id: boolComponent
        CheckBox {
            checked: attribute ? attribute.value : false
            padding: 12
            enabled: !readOnly
            onToggled: _reconstruction.setAttribute(attribute, !attribute.value)
        }
    }

    Component {
        id: floatComponent
        TextInput {
            readonly property real formattedValue: attribute.value.toFixed(2)
            property string displayValue: String(formattedValue)

            text: displayValue
            width: intrinsicModel.columnWidths[columnIndex]
            horizontalAlignment: TextInput.AlignRight

            color: palette.text
            padding: 12

            selectByMouse: true
            selectionColor: palette.text
            selectedTextColor: Qt.darker(palette.window, 1.1)

            readOnly: root.readOnly
            enabled: !readOnly

            clip: true

            autoScroll: activeFocus

            // Use this function to ensure the left part is visible
            // while keeping the trick for formatting the text
            // Timing issues otherwise
            onActiveFocusChanged: {
                if (activeFocus)
                    text = String(attribute.value)
                else
                    text = String(formattedValue)
                cursorPosition = 0
            }

            DoubleValidator {
                id: doubleValidator
                locale: 'C'  // Use '.' decimal separator disregarding the system locale
            }

            validator: doubleValidator

            onEditingFinished: _reconstruction.setAttribute(attribute, Number(text))
            onAccepted: {
                _reconstruction.setAttribute(attribute, Number(text))
            }
            Component.onDestruction: {
                if (activeFocus)
                    _reconstruction.setAttribute(attribute, Number(text))
            }
        }
    }
}
