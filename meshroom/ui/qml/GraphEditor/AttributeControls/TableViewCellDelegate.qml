import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import MaterialIcons 2.2
import Utils 1.0

import "../AttributeFunctions" as AttributeFunctions

Rectangle {
    id: cellRect
    property int cellIndex: 0
    property var rowObject: null
    property int rowIndex: 0
    property real cellWidth: 100
    property real cellHeight: 24
    property bool editable: true
    property bool cellReady: false
    property real minCellWidth: 60
    signal loaderReady()
    width: cellWidth
    height: cellHeight
    color: palette.window
    border.color: palette.mid
    clip: true
    property var cell: rowObject
                       ? rowObject.value.at(cellIndex)
                       : null
    Rectangle {
        anchors.centerIn: parent
        width: cellLoader.width + 8
        height: cellLoader.height + 4
        radius: 3
        color: palette.base
        visible: cellRect.cell &&
                 (cellRect.cell.type === "BoolParam" ||
                  cellRect.cell.type === "ChoiceParam")
    }
    Loader {
        id: cellLoader
        property bool isCheckbox: attribute && attribute.type === "BoolParam"
        anchors.fill: isCheckbox ? undefined : parent
        anchors.centerIn: isCheckbox ? parent : undefined
        property var attribute: cellRect.cell
        onStatusChanged: {
            if (status !== Loader.Ready)
                return
            cellRect.minCellWidth = (item && item.minWidth !== undefined)
                                    ? item.minWidth
                                    : 60
            cellRect.cellReady = true
            cellRect.loaderReady()
        }
        AttributeFunctions.SetAttribute {
            id: setAttributeHelper
        }
        function setTextFieldAttribute(value) {
            setAttributeHelper.setTextFieldAttribute(cellLoader.attribute, value, cellRect.editable, _currentScene, _currentScene.selectedViewId)
        }
        sourceComponent: {
            if (!attribute)
                return null
            switch (attribute.type) {
                case "PushButtonParam":
                    return pushButtonComponent
                case "ChoiceParam":
                    return (attribute.desc && attribute.desc.exclusive)
                           ? choiceComponent
                           : choiceMultiComponent
                case "IntParam":
                    return sliderComponent
                case "FloatParam":
                    return (attribute.desc &&
                            attribute.desc.semantic === "color/hue")
                           ? colorHueComponent
                           : sliderComponent
                case "BoolParam":
                    return checkboxComponent
                case "StringParam":
                    return (attribute.desc && attribute.desc.semantic &&
                            attribute.desc.semantic.includes("multiline"))
                           ? textAreaComponent
                           : textFieldComponent
                case "ColorParam":
                    return colorComponent
                default:
                    return textFieldComponent
            }
        }
        Component {
            id: pushButtonComponent
            Button {
                text: cellLoader.attribute.label
                enabled: cellRect.editable
                onClicked: {
                    cellLoader.attribute.clicked()
                }
            }
        }
        Component {
            id: choiceComponent
            Choice {
                value: cellLoader.attribute.value
                values: cellLoader.attribute.values
                enabled: cellRect.editable
                onEditingFinished: (value) => {
                    _currentScene.setAttribute(cellLoader.attribute, value)
                }
            }
        }
        Component {
            id: choiceMultiComponent
            ChoiceMulti {
                value: cellLoader.attribute.value
                values: cellLoader.attribute.values
                enabled: cellRect.editable
                customValueColor: Colors.orange
                onToggled: (value, checked) => {
                    var currentValue = cellLoader.attribute.value;
                    if (!checked) {
                        currentValue.splice(currentValue.indexOf(value), 1);
                    } else {
                        currentValue.push(value);
                    }
                    _currentScene.setAttribute(cellLoader.attribute, currentValue);
                }
            }
        }
        Component {
            id: sliderComponent
            SliderField {
                checked: cellLoader.attribute.keyable
                                ? cellLoader.attribute.keyValues.getValueAtKeyOrDefault(_currentScene.selectedViewId)
                                : cellLoader.attribute.value
                type: cellLoader.attribute.type
                length: (cellLoader.attribute.desc.range && cellLoader.attribute.desc.range.length) || 0
                start: (cellLoader.attribute.desc.range && cellLoader.attribute.desc.range[0]) || 0
                end: (cellLoader.attribute.desc.range && cellLoader.attribute.desc.range[1]) || 0
                step: (cellLoader.attribute.desc.range && cellLoader.attribute.desc.range[2]) || 0
                editable: cellRect.editable
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
                Component.onDestruction: (activeFocus, hasExprError, evaluatedValue) =>  {
                    if (activeFocus) {
                        if (!hasExprError)
                            setTextFieldAttribute(evaluatedValue)
                    }
                }
                onPressedChanged: (pressed, formattedValue) => {
                    if (!pressed) {
                        if (cellLoader.attribute.keyable)
                            _currentScene.addAttributeKeyValue(cellLoader.attribute, _currentScene.selectedViewId, formattedValue)
                        else
                            _currentScene.setAttribute(cellLoader.attribute, formattedValue)
                    }
                }
            }
        }
        Component {
            id: colorHueComponent
            ColorHue {
                value: cellLoader.attribute.value
                editable: cellRect.editable
                onEditingFinished: (text) => setTextFieldAttribute(text)
                onAccepted: (text) => setTextFieldAttribute(text)
                onDestruction: (activeFocus, text) => {
                    if (activeFocus)
                        setTextFieldAttribute(text)
                }
                onPressedChanged: (pressed, formattedValue) => {
                    if (!pressed)
                        _currentScene.setAttribute(cellLoader.attribute, formattedValue)
                }
            }
        }
        Component {
            id: checkboxComponent
            CheckBoxRow {
                editable: cellRect.editable
                checked: cellLoader.attribute.keyable
                                ? cellLoader.attribute.keyValues.getValueAtKeyOrDefault(_currentScene.selectedViewId)
                                : cellLoader.attribute.value
                onToggled: {
                    if(cellLoader.attribute.keyable)
                    {
                        const value = cellLoader.attribute.keyValues.getValueAtKeyOrDefault(_currentScene.selectedViewId)
                        _currentScene.addAttributeKeyValue(cellLoader.attribute, _currentScene.selectedViewId, !value)
                    }
                    else
                    {
                        _currentScene.setAttribute(cellLoader.attribute, !cellLoader.attribute.value)
                    }
                }
            }
        }
        Component {
            id: textFieldComponent
            TextFieldRow {
                text: cellLoader.attribute
                      ? String(cellLoader.attribute.value)
                      : ""
                mandatory: cellLoader.attribute.isMandatory
                editable: cellRect.editable
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
                label: cellLoader.attribute.value
                isLarge: cellLoader.attribute.desc.semantic.includes("large")
                editable: cellRect.editable
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
                value: cellLoader.attribute.value
                editable: cellRect.editable
                onClicked: (checked, previousColor, colorTextValue) =>{
                    if (checked) {
                        if (colorTextValue == "") {
                            if (previousColor !== "")
                                _currentScene.setAttribute(cellLoader.attribute, previousColor)
                            else
                                _currentScene.setAttribute(cellLoader.attribute, "#0000FF")
                        }
                        else
                            _currentScene.setAttribute(cellLoader.attribute, colorTextValue)
                    } else {
                        colorControl.previousColor = cellLoader.attribute.value
                        _currentScene.setAttribute(cellLoader.attribute, "")
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
}
