import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Utils

RowLayout {
    id: root
    required property var checked
    required property var type
    required property int length
    required property int start
    required property int end
    required property int step
    property bool editable
    signal editingFinished(bool hasExprError, var evaluatedValue, var text, var displayValue)
    signal accepted(bool hasExprError, var evaluatedValue, var text, var displayValue)
    signal destruction(bool activeFocus, bool hasExprError, var text)
    signal pressedChanged(bool pressed, var formattedValue)

    ExpressionTextField {
        id: expressionTextField
        implicitWidth: 100
        Layout.fillWidth: !slider.active
        enabled: root.editable
        // Cast value to string to avoid intrusive scientific notations on numbers
        property string displayValue: String(slider.active && slider.item.pressed ? slider.item.formattedValue : checked)
        text: displayValue
        selectByMouse: true
        // Note: Use autoScroll as a workaround for alignment
        // When the value change keep the text align to the left to be able to read the most important part
        // of the number. When we are editing (item is in focus), the content should follow the editing.
        autoScroll: activeFocus
        isInt: root.type === "FloatParam" ? false : true
        onEditingFinished: root.editingFinished(hasExprError, expressionTextField.evaluatedValue, expressionTextField.text, expressionTextField.displayValue)
        background: Rectangle {
                border.width: expressionTextField.activeFocus ? 2 : 1
                border.color: expressionTextField.activeFocus ? palette.highlight : (errorMessages.length ? "orange" : "transparent")
                color: Qt.darker(palette.window, 1.2)
                radius: 2
            }
        onAccepted: {
            root.accepted(hasExprError, expressionTextField.evaluatedValue, expressionTextField.text, expressionTextField.displayValue)
            // When the text is too long, display the left part
            // (with the most important values and cut the floating point details)
            ensureVisible(0)
        }
        Component.onDestruction: root.destruction(activeFocus, hasExprError, expressionTextField.evaluatedValue)
        Component.onCompleted: {
            // When the text is too long, display the left part
            // (with the most important values and cut the floating point details)
            ensureVisible(0)
        }

        WheelHandler {
            id: expressionWheelHandler
            enabled: root.editable && expressionTextField.activeFocus
            onWheel: (event) => {
                var stepValue = root.length === 3 ? root.step : (root.type === "FloatParam" ? 0.01 : 1)
                if (event.modifiers & Qt.ShiftModifier)
                    stepValue *= 10
                var delta = (event.angleDelta.y > 0 ? stepValue : -stepValue)
                var newVal = Number(root.checked) + delta
                if (root.length === 3)
                    newVal = Math.max(root.start, Math.min(root.end, newVal))
                if (root.type !== "FloatParam")
                    newVal = Math.round(newVal)
                var text = String(newVal)
                root.editingFinished(false, newVal, text, text)
                root.accepted(false, newVal, text, text)
            }
        }
    }

    Loader {
        id: slider
        Layout.fillWidth: true
        active: root.length === 3
        sourceComponent: Slider {
            id: sliderItem
            readonly property int stepDecimalCount: stepSize <  1 ? String(stepSize).split(".").pop().length : 0
            readonly property real formattedValue: value.toFixed(stepDecimalCount)
            enabled: root.editable
            focusPolicy: Qt.StrongFocus
            value: root.checked
            from: root.start
            to: root.end
            stepSize: root.step
            snapMode: Slider.SnapAlways
            onPressedChanged: root.pressedChanged(pressed, formattedValue)
        }
    }
}