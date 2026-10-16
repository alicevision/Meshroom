import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

/**
 * Editor of a 2D attribute (desc.Vec2d: {x, y}): x and y fields, set together as one undoable change.
 *
 * With the "linkedVec2" semantic, the attribute is edited as a single value by default (x = y, e.g.
 * a scale or a blur size), and a "split" checkbox shows x and y apart. Values that differ (e.g. loaded
 * from a file) are always shown split. The checkbox state is remembered for the session.
 */
RowLayout {
    id: root

    required property var attribute
    property bool editable: true
    readonly property bool linkable: attribute.desc.semantic === "linkedVec2"
    readonly property var xAttribute: attribute.value ? attribute.value.get("x") : null
    readonly property var yAttribute: attribute.value ? attribute.value.get("y") : null
    readonly property real xValue: xAttribute ? xAttribute.value : 0
    readonly property real yValue: yAttribute ? yAttribute.value : 0
    readonly property var range: xAttribute && xAttribute.desc.range ? xAttribute.desc.range : []
    property bool splitChecked: _currentScene ? _currentScene.isVec2Split(attribute) : false
    readonly property bool valuesDiffer: Math.abs(xValue - yValue) > 1e-9
    // Frozen while the values are being set: x and y change one after the other, and a transient
    // difference must not replace the single field being edited
    property bool editing: false
    property bool frozenSplit: false
    readonly property bool split: editing ? frozenSplit : (!linkable || splitChecked || valuesDiffer)

    spacing: 2

    function setValues(x, y) {
        x = Number(x)
        y = Number(y)
        if (!isFinite(x) || !isFinite(y) || (Math.abs(x - xValue) < 1e-12 && Math.abs(y - yValue) < 1e-12))
            return
        frozenSplit = split
        editing = true
        _currentScene.setVec2Attribute(root.attribute, x, y)
        editing = false
    }

    function setSplit(split) {
        if (!split && valuesDiffer)
            setValues(xValue, xValue)
        _currentScene.setVec2Split(root.attribute, split)
        splitChecked = split
    }

    // Linked: a single field for both values
    SliderField {
        id: linkedField
        visible: !root.split
        Layout.fillWidth: true
        checked: root.xValue
        type: "FloatParam"
        length: root.range.length || 0
        start: root.range[0] || 0
        end: root.range[1] || 0
        step: root.range[2] || 0
        editable: root.editable
        // A hidden field never writes (e.g. when it loses the focus after a split)
        onEditingFinished: (hasExprError, evaluatedValue, text, displayValue) => {
            if (!hasExprError && linkedField.visible)
                root.setValues(evaluatedValue, evaluatedValue)
        }
        onAccepted: (hasExprError, evaluatedValue, text, displayValue) => {
            if (!hasExprError && linkedField.visible)
                root.setValues(evaluatedValue, evaluatedValue)
        }
        onPressedChanged: (pressed, formattedValue) => {
            if (!pressed && linkedField.visible)
                root.setValues(formattedValue, formattedValue)
        }
    }

    // Split: x and y fields
    Label { visible: root.split; text: "x"; opacity: 0.6 }
    SliderField {
        id: xField
        visible: root.split
        Layout.fillWidth: true
        checked: root.xValue
        type: "FloatParam"
        length: root.range.length || 0
        start: root.range[0] || 0
        end: root.range[1] || 0
        step: root.range[2] || 0
        editable: root.editable
        onEditingFinished: (hasExprError, evaluatedValue, text, displayValue) => {
            if (!hasExprError && xField.visible)
                root.setValues(evaluatedValue, root.yValue)
        }
        onAccepted: (hasExprError, evaluatedValue, text, displayValue) => {
            if (!hasExprError && xField.visible)
                root.setValues(evaluatedValue, root.yValue)
        }
        onPressedChanged: (pressed, formattedValue) => {
            if (!pressed && xField.visible)
                root.setValues(formattedValue, root.yValue)
        }
    }
    Label { visible: root.split; text: "y"; opacity: 0.6 }
    SliderField {
        id: yField
        readonly property var yRange: root.yAttribute && root.yAttribute.desc.range ? root.yAttribute.desc.range : []
        visible: root.split
        Layout.fillWidth: true
        checked: root.yValue
        type: "FloatParam"
        length: yRange.length || 0
        start: yRange[0] || 0
        end: yRange[1] || 0
        step: yRange[2] || 0
        editable: root.editable
        onEditingFinished: (hasExprError, evaluatedValue, text, displayValue) => {
            if (!hasExprError && yField.visible)
                root.setValues(root.xValue, evaluatedValue)
        }
        onAccepted: (hasExprError, evaluatedValue, text, displayValue) => {
            if (!hasExprError && yField.visible)
                root.setValues(root.xValue, evaluatedValue)
        }
        onPressedChanged: (pressed, formattedValue) => {
            if (!pressed && yField.visible)
                root.setValues(root.xValue, formattedValue)
        }
    }

    CheckBox {
        visible: root.linkable
        enabled: root.editable
        text: "split"
        font.pointSize: 8
        padding: 0
        checked: root.split
        ToolTip.text: checked ? "Uncheck: a single value (y = x)" : "Check: edit x and y separately"
        ToolTip.visible: hovered
        onClicked: {
            root.setSplit(!root.split)
            // The click toggled the box: it follows the state again
            checked = Qt.binding(function() { return root.split })
        }
    }
}
