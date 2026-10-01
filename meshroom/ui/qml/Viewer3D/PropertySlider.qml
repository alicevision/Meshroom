import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import MaterialIcons 2.2

/**
 * Slider row editing the numeric property @p propertyName of @p target.
 * Shows a text @p label or a MaterialIcons @p icon, the slider and optionally the current value.
 * Displays @p defaultValue and is disabled while @p target is null or lacks the property.
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
    property alias from: slider.from
    property alias to: slider.to
    property alias stepSize: slider.stepSize

    readonly property bool hasProperty: target !== null && target[propertyName] !== undefined
    readonly property real value: hasProperty ? target[propertyName] : defaultValue

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
        value: root.value
        onMoved: root.target[root.propertyName] = value
        ToolTip.text: root.toolTipName + ": " + value.toFixed(root.decimals)
        ToolTip.visible: hovered || pressed
        ToolTip.delay: 100
    }

    Label {
        visible: root.showValue
        text: root.value.toFixed(root.decimals)
        color: palette.text
    }
}
