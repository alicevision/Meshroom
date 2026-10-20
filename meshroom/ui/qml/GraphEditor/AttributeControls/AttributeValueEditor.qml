import QtQuick
import QtQuick.Controls

import Utils 1.0
import "." as AttributeControls

/**
 * AttributeValueEditor loads the control matching the type of a non-container attribute
 * and forwards its edits to the current scene.
 * Containers (ListAttribute, GroupAttribute...) are not handled here: users can override
 * 'sourceComponent' and fall back on 'valueComponent' for other attribute types.
 */

Loader {
    id: root

    required property var attribute
    property bool editable: true

    readonly property Component valueComponent: {
        if (!root.attribute)
            return null
        // PushButtonParam always has value == undefined, so it needs to be excluded from this check
        if (root.attribute.type != "PushButtonParam" && root.attribute.type != "Flow" && !root.attribute.keyable && root.attribute.value === undefined)
            return notComputedComponent
        switch (root.attribute.type) {
            case "PushButtonParam":
                return pushButtonComponent
            case "ChoiceParam":
                return root.attribute.desc.exclusive ? choiceComponent : choiceMultiComponent
            case "IntParam":
                return sliderComponent
            case "FloatParam":
                return root.attribute.desc.semantic === "color/hue" ? colorHueComponent : sliderComponent
            case "BoolParam":
                return checkboxComponent
            case "StringParam":
                return root.attribute.desc.semantic.includes("multiline") ? textAreaComponent : textFieldComponent
            case "ColorParam":
                return colorComponent
            case "Flow":
                return flowComponent
            default:
                return textFieldComponent
        }
    }

    sourceComponent: valueComponent

    function setTextFieldAttribute(value) {
        // editingFinished called even when TextField is readonly
        if (!root.editable)
            return
        switch (root.attribute.type) {
            case "IntParam":
            case "FloatParam":
                // We do not set a number because we want to keep the invalid expression
                if (root.attribute.keyable)
                    _currentScene.addAttributeKeyValue(root.attribute, _currentScene.selectedViewId, Number(value))
                else
                    _currentScene.setAttribute(root.attribute, Number(value))
                break
            case "File":
                _currentScene.setAttribute(root.attribute, value)
                break
            default:
                _currentScene.setAttribute(root.attribute, value.trim())
                break
        }
    }

    Component {
        id: notComputedComponent
        AttributeControls.NotComputed {}
    }

    Component {
        id: pushButtonComponent
        Button {
            text: root.attribute.label
            enabled: root.editable
            onClicked: {
                root.attribute.clicked()
            }
        }
    }

    Component {
        id: flowComponent
        // Flow has no data to display; connection state is shown via the attribute pin
        Item {}
    }

    Component {
        id: textFieldComponent
        AttributeControls.TextFieldRow {
            text: root.attribute.value
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
                setTextFieldAttribute(before + clipboard + after)
            }
        }
    }

    Component {
        id: textAreaComponent
        AttributeControls.TextAreaFlick {
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
        AttributeControls.Color {
            id: colorControl
            value: root.attribute.value
            editable: root.editable
            onClicked: (checked, previousColor, colorTextValue) =>{
                if (checked) {
                    if (colorTextValue == "") {
                        if (previousColor !== "")
                            _currentScene.setAttribute(root.attribute, previousColor)
                        else
                            _currentScene.setAttribute(root.attribute, "#0000FF")
                    }
                    else
                        _currentScene.setAttribute(root.attribute, colorTextValue)
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

    Component {
        id: choiceComponent

        AttributeControls.Choice {
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

        AttributeControls.ChoiceMulti {
            value: root.attribute.value
            values: root.attribute.values
            enabled: root.editable
            customValueColor: Colors.orange

            onToggled: (value, checked) => {
                var currentValue = root.attribute.value;
                if (!checked) {
                    currentValue.splice(currentValue.indexOf(value), 1);
                } else {
                    currentValue.push(value);
                }
                _currentScene.setAttribute(root.attribute, currentValue);
            }
        }
    }

    Component {
        id: sliderComponent
        AttributeControls.SliderField {
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
            Component.onDestruction: (activeFocus, hasExprError, displayValue) =>  {
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
        id: checkboxComponent
        AttributeControls.CheckBoxRow {
            editable: root.editable
            checked: root.attribute.keyable
                            ? root.attribute.keyValues.getValueAtKeyOrDefault(_currentScene.selectedViewId)
                            : root.attribute.value
            onToggled: {
                if(root.attribute.keyable)
                {
                    const value = root.attribute.keyValues.getValueAtKeyOrDefault(_currentScene.selectedViewId)
                    _currentScene.addAttributeKeyValue(root.attribute, _currentScene.selectedViewId, !value)
                }
                else
                {
                    _currentScene.setAttribute(root.attribute, !root.attribute.value)
                }
            }
        }
    }

    Component {
        id: colorHueComponent
        AttributeControls.ColorHue {
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
}
