import QtQuick
import QtQuick.Controls
import Controls

/**
 * A multi-checkboxes control with a current `value` (list of 0-N elements) and a list of possible `values`.
 * Provides support for custom values (`value` elements not in `values`).
 */
Flow {
    id: root

    required property var value
    required property var values
    property color customValueColor: "orange"

    signal toggled(var value, var checked)

    // Predefined possible values.
    Repeater {
        model: root.values
        delegate: CheckBox {
            id: checkBoxDelegate
            text: modelData
            checked: root.value.includes(modelData)
            onToggled: root.toggled(modelData, checked)
            indicator: Rectangle {
                implicitWidth: 16
                implicitHeight: 16
                x: checkBoxDelegate.leftPadding
                y: checkBoxDelegate.height / 2 - height / 2
                radius: 2
                color: checkBoxDelegate.palette.base
                border.width: checkBoxDelegate.activeFocus ? 2 : 0
                border.color: checkBoxDelegate.activeFocus ? checkBoxDelegate.palette.highlight : checkBoxDelegate.palette.mid

                Rectangle {
                    width: 8
                    height: 8
                    x: 4
                    y: 4
                    radius: 1
                    color: checkBoxDelegate.palette.text
                    visible: checkBoxDelegate.checked
                }
            }
        }
    }

    // Custom elements outside the predefined possible values.
    Repeater {
        model: root.value.filter(v => !root.values.includes(v))
        delegate: CheckBox {
            id: customCheckBoxDelegate
            text: modelData
            palette.text: root.customValueColor
            font.italic: true
            checked: true
            ToolTip.text: "Custom value"
            ToolTip.visible: hovered
            onToggled: root.toggled(modelData, checked)
            indicator: Rectangle {
                implicitWidth: 16
                implicitHeight: 16
                x: customCheckBoxDelegate.leftPadding
                y: customCheckBoxDelegate.height / 2 - height / 2
                radius: 2
                color: customCheckBoxDelegate.palette.base
                border.width: customCheckBoxDelegate.activeFocus ? 2 : 0
                border.color: customCheckBoxDelegate.activeFocus ? customCheckBoxDelegate.palette.highlight : customCheckBoxDelegate.palette.mid

                Rectangle {
                    width: 8
                    height: 8
                    x: 4
                    y: 4
                    radius: 1
                    color: customCheckBoxDelegate.palette.text
                    visible: customCheckBoxDelegate.checked
                }
            }
        }
    }
}