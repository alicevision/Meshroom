import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import MaterialIcons 2.2

/**
 * Slider row editing the numeric property @p propertyName of @p target.
 * Shows a text @p label or a MaterialIcons @p icon, the slider and optionally the current value.
 * Displays @p defaultValue and is disabled while @p target is null or lacks the property.
 * With @p logarithmic, the slider moves along log10 of the value (@p from must be > 0), giving the same
 * precision across several orders of magnitude; values are then rounded to 2 significant digits
 * and @p stepSize is expressed in log10 units.
 */
RowLayout {
    id: root

    property var target: null
    property string propertyName: ""
    property real defaultValue: 0
    property string label: ""
    property string icon: ""
    property string toolTipName: label
    property int labelWidth: 42
    property int decimals: 2
    property bool showValue: true
    property real from: 0
    property real to: 1
    property alias stepSize: slider.stepSize
    property bool logarithmic: false

    readonly property bool hasProperty: target !== null && target[propertyName] !== undefined
    readonly property real value: hasProperty ? target[propertyName] : defaultValue

    /** Convert a property value to a slider position. */
    function toSlider(v) {
        return logarithmic ? Math.log10(v) : v
    }

    /** Convert a slider position to a property value. */
    function fromSlider(v) {
        return logarithmic ? Number(Math.pow(10, v).toPrecision(2)) : v
    }

    function formatValue(v) {
        return logarithmic ? String(Number(v.toPrecision(2))) : v.toFixed(decimals)
    }

    spacing: 4

    Label {
        visible: root.icon.length === 0
        text: root.label
        color: palette.text
        Layout.preferredWidth: root.labelWidth
    }

    MaterialLabel {
        visible: root.icon.length > 0
        text: root.icon
        padding: 2
    }

    Slider {
        id: slider
        Layout.fillWidth: true
        enabled: root.hasProperty
        from: root.toSlider(root.from)
        to: root.toSlider(root.to)
        value: root.toSlider(root.value)
        onMoved: root.target[root.propertyName] = root.fromSlider(value)
        ToolTip.text: root.toolTipName + ": " + root.formatValue(root.fromSlider(value))
        ToolTip.visible: hovered || pressed
        ToolTip.delay: 100
    }

    Label {
        id: valueLabel
        visible: root.showValue
        text: root.formatValue(root.value)
        color: palette.text
        // Fixed width in logarithmic mode, so that the slider does not move as the number of digits changes
        Layout.minimumWidth: root.logarithmic ? widestValue.advanceWidth : 0
        horizontalAlignment: Text.AlignRight

        TextMetrics {
            id: widestValue
            font: valueLabel.font
            text: "0.00"
        }
    }
}
