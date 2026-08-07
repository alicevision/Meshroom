import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Utils

RowLayout {
	id: root
	required property var attribute
	property bool editable
    ExpressionTextField {
        id: expressionTextField
        implicitWidth: 100
        Layout.fillWidth: !slider.active
        enabled: root.editable
        // Cast value to string to avoid intrusive scientific notations on numbers
        property string displayValue: String(slider.active && slider.item.pressed ? slider.item.formattedValue :
                                            attribute.keyable ? attribute.keyValues.getValueAtKeyOrDefault(_currentScene.selectedViewId) :
                                            attribute.value)
        text: displayValue
        selectByMouse: true
        // Note: Use autoScroll as a workaround for alignment
        // When the value change keep the text align to the left to be able to read the most important part
        // of the number. When we are editing (item is in focus), the content should follow the editing.
        autoScroll: activeFocus
        isInt: attribute.type === "FloatParam" ? false : true
        onEditingFinished: {
            if (!hasExprError) {
                setTextFieldAttribute(root.attribute, expressionTextField.evaluatedValue)
                // Restore binding
                expressionTextField.text = Qt.binding(function() { return String(expressionTextField.displayValue); })
            }
        }
        background: Rectangle {
                border.color: errorMessages.length ? "orange" : "transparent"
                color: Qt.darker(palette.window, 1.2)
                radius: 2
            }
        onAccepted: {
            if (!hasExprError) {
                setTextFieldAttribute(root.attribute, expressionTextField.evaluatedValue)
                // Restore binding
                expressionTextField.text = Qt.binding(function() { return String(expressionTextField.displayValue); })
            }
            // When the text is too long, display the left part
            // (with the most important values and cut the floating point details)
            ensureVisible(0)
        }
        Component.onDestruction: {
            if (activeFocus) {
                if (!hasExprError)
                    setTextFieldAttribute(root.attribute, expressionTextField.evaluatedValue)
            }
        }
        Component.onCompleted: {
            // When the text is too long, display the left part
            // (with the most important values and cut the floating point details)
            ensureVisible(0)
        }
    }
    Loader {
        id: slider
        Layout.fillWidth: true
        active: attribute.desc.range.length === 3
        sourceComponent: Slider {
            readonly property int stepDecimalCount: stepSize <  1 ? String(stepSize).split(".").pop().length : 0
            readonly property real formattedValue: value.toFixed(stepDecimalCount)
            enabled: root.editable
            value: attribute.keyable ? attribute.keyValues.getValueAtKeyOrDefault(_currentScene.selectedViewId) : attribute.value
            from: attribute.desc.range[0]
            to: attribute.desc.range[1]
            stepSize: attribute.desc.range[2]
            snapMode: Slider.SnapAlways
            onPressedChanged: {
                if (!pressed) {
                    if (attribute.keyable)
                        _currentScene.addAttributeKeyValue(attribute, _currentScene.selectedViewId, formattedValue)
                    else
                        _currentScene.setAttribute(attribute, formattedValue)
                }
            }
        }
    }
}