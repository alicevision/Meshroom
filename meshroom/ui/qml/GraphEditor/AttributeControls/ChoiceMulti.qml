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
            text: modelData
            checked: root.value.includes(modelData)
            onToggled: root.toggled(modelData, checked)
        }
    }

    // Custom elements outside the predefined possible values.
    Repeater {
        model: root.value.filter(v => !root.values.includes(v))
        delegate: CheckBox {
            text: modelData
            palette.text: root.customValueColor
            font.italic: true
            checked: true
            ToolTip.text: "Custom value"
            ToolTip.visible: hovered
            onToggled: root.toggled(modelData, checked)
        }
    }
}
