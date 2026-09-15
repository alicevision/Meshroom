import QtQuick
import QtQuick.Controls

import Utils 1.0

import "../AttributeFunctions" as AttributeFunctions

/**
 * Loader that instantiates the control used to visualize and edit the value of a
 * scalar Attribute, based on its type.
 *
 * Shared by AttributeItemDelegate.qml (single attribute rows) and
 * TableViewCellDelegate.qml (table cells), so both stay in sync automatically.
 */
Loader {
    id: root

    property var attribute: null
    property bool editable: true
    readonly property real minWidth: (item && item.minWidth !== undefined) ? item.minWidth : 0

    AttributeFunctions.SetAttribute {
        id: setAttributeHelper
    }
    function setTextFieldAttribute(value) {
        setAttributeHelper.setTextFieldAttribute(root.attribute, value, root.editable, _currentScene, _currentScene.selectedViewId)
    }

    sourceComponent: {
        if (!attribute)
            return null
        switch (attribute.type) {
            case "PushButtonParam":
                return pushButtonComponent
            case "ChoiceParam":
                return (attribute.desc && attribute.desc.exclusive) ? choiceComponent : choiceMultiComponent
            case "IntParam":
                return sliderComponent
            case "FloatParam":
                return (attribute.desc && attribute.desc.semantic === "color/hue") ? colorHueComponent : sliderComponent
            case "BoolParam":
                return checkboxComponent
            case "StringParam":
                return (attribute.desc && attribute.desc.semantic && attribute.desc.semantic.includes("multiline")) ? textAreaComponent : textFieldComponent
            case "ColorParam":
                return colorComponent
            default:
                return textFieldComponent
        }
    }

    Component {
        id: pushButtonComponent
        Button {
            text: root.attribute.label
            enabled: root.editable
            onClicked: root.attribute.clicked()
        }
    }

    Component {
        id: choiceComponent
        Choice {
            value: root.attribute.value
            values: root.attribute.values
            enabled: root.editable
            onEditingFinished: (value) => {
                _currentScene.setAttribute(root.attribute, value)
            }
        }
    }

    Component {
        id: choiceMultiComponent
        ChoiceMulti {
            value: root.attribute.value
            values: root.attribute.values
            enabled: root.editable
            customValueColor: Colors.orange
            onToggled: (value, checked) => {
                var currentValue = root.attribute.value
                if (!checked) {
                    currentValue.splice(currentValue.indexOf(value), 1)
                } else {
                    currentValue.push(value)
                }
                _currentScene.setAttribute(root.attribute, currentValue)
            }
        }
    }

    Component {
        id: sliderComponent
        SliderField {
            checked: root.attribute.keyable
                            ? root.attribute.keyValues.getValueAtKeyOrDefault(_currentScene.selectedViewId)
                            : root.attribute.value
            type: root.attribute.type
            length: (root.attribute.desc.range && root.attribute.desc.range.length) || 0
            start: (root.attribute.desc.range && root.attribute.desc.range[0]) || 0
            end: (root.attribute.desc.range && root.attribute.desc.range[1]) || 0
            step: (root.attribute.desc.range && root.attribute.desc.range[2]) || 0
            editable: root.editable
            onEditingFinished: (hasExprError, evaluatedValue, text, displayValue) => {
                if (!hasExprError) {
                    setTextFieldAttribute(evaluatedValue)
                    // Restore binding
                    text = Qt.binding(function() { return String(displayValue); })
                }
            }
            onAccepted: (hasExprError, evaluatedValue, text, displayValue) => {
                if (!hasExprError) {
                    setTextFieldAttribute(evaluatedValue)
                    // Restore binding
                    text = Qt.binding(function() { return String(displayValue); })
                }
            }
            Component.onDestruction: (activeFocus, hasExprError, evaluatedValue) => {
                if (activeFocus) {
                    if (!hasExprError)
                        setTextFieldAttribute(evaluatedValue)
                }
            }
            onPressedChanged: (pressed, formattedValue) => {
                if (!pressed) {
                    if (root.attribute.keyable)
                        _currentScene.addAttributeKeyValue(root.attribute, _currentScene.selectedViewId, formattedValue)
                    else
                        _currentScene.setAttribute(root.attribute, formattedValue)
                }
            }
        }
    }

    Component {
        id: colorHueComponent
        ColorHue {
            value: root.attribute.value
            editable: root.editable
            onEditingFinished: (text) => setTextFieldAttribute(text)
            onAccepted: (text) => setTextFieldAttribute(text)
            onDestruction: (activeFocus, text) => {
                if (activeFocus)
                    setTextFieldAttribute(text)
            }
            onPressedChanged: (pressed, formattedValue) => {
                if (!pressed)
                    _currentScene.setAttribute(root.attribute, formattedValue)
            }
        }
    }

    Component {
        id: checkboxComponent
        CheckBoxRow {
            editable: root.editable
            checked: root.attribute.keyable
                            ? root.attribute.keyValues.getValueAtKeyOrDefault(_currentScene.selectedViewId)
                            : root.attribute.value
            onToggled: {
                if (root.attribute.keyable) {
                    const value = root.attribute.keyValues.getValueAtKeyOrDefault(_currentScene.selectedViewId)
                    _currentScene.addAttributeKeyValue(root.attribute, _currentScene.selectedViewId, !value)
                } else {
                    _currentScene.setAttribute(root.attribute, !root.attribute.value)
                }
            }
        }
    }

    Component {
        id: textFieldComponent
        TextFieldRow {
            text: root.attribute ? String(root.attribute.value) : ""
            mandatory: root.attribute.isMandatory
            editable: root.editable
            onEditingFinished: (text) => setTextFieldAttribute(text)
            onAccepted: (parameterLabel, text) => {
                setTextFieldAttribute(text)
                parameterLabel.forceActiveFocus()
            }
            onDestruction: (activeFocus, text) => {
                if (activeFocus)
                    setTextFieldAttribute(text)
            }
            onDropped: (hasUrls, hasText, urlText, text) => {
                if (hasUrls)
                    setTextFieldAttribute(urlText)
                else if (hasText)
                    setTextFieldAttribute(text)
            }
            onTriggered: (text, start, end, length, clipboard) => {
                const before = text.substr(0, start)
                const after = text.substr(end, length)
                const updatedValue = before + clipboardText + after
                setTextFieldAttribute(updatedValue)
                // Set the cursor at the end of the added text
                textField.cursorPosition = before.length + clipboard.length
            }
        }
    }

    Component {
        id: textAreaComponent
        TextAreaFlick {
            label: root.attribute.value
            isLarge: root.attribute.desc.semantic.includes("large")
            editable: root.editable
            onEditingFinished: (text) => setTextFieldAttribute(text)
            onDestruction: (activeFocus, text) => {
                if (activeFocus)
                    setTextFieldAttribute(text)
            }
            onDropped: (hasUrls, hasText, urlText, text) => {
                if (hasUrls)
                    setTextFieldAttribute(urlText)
                else if (hasText)
                    setTextFieldAttribute(text)
            }
        }
    }

    Component {
        id: colorComponent
        Color {
            id: colorControl
            value: root.attribute.value
            editable: root.editable
            onClicked: (checked, previousColor, colorTextValue) => {
                if (checked) {
                    if (colorTextValue == "") {
                        if (previousColor !== "")
                            _currentScene.setAttribute(root.attribute, previousColor)
                        else
                            _currentScene.setAttribute(root.attribute, "#0000FF")
                    } else {
                        _currentScene.setAttribute(root.attribute, colorTextValue)
                    }
                } else {
                    colorControl.previousColor = root.attribute.value
                    _currentScene.setAttribute(root.attribute, "")
                }
            }
            onEditingFinished: (text) => setTextFieldAttribute(text)
            onAccepted: (text) => setTextFieldAttribute(text)
            onDestruction: (activeFocus, text) => {
                if (activeFocus)
                    setTextFieldAttribute(text)
            }
        }
    }
}
