import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import MaterialIcons 2.2

/**
 * Editor of an RGBA color attribute: a GroupAttribute of 4 FloatParams r, g, b, a with the "rgbaColor"
 * semantic (linear values, not limited to [0, 1]). A swatch over a checkerboard (its alpha) with the
 * values, and a slider per channel.
 *
 * With the "linkedColor" semantic (a value per channel, e.g. a gain), a single slider sets the 4
 * channels by default and a "split" checkbox shows the channels apart (remembered for the session);
 * channels that differ are always shown apart.
 */
ColumnLayout {
    id: root

    required property var attribute
    property bool editable: true
    readonly property bool linkable: attribute.desc.semantic === "linkedColor"
    property bool expanded: linkable

    property bool splitChecked: _currentScene ? _currentScene.isRgbaSplit(attribute) : false
    readonly property bool valuesDiffer: Math.abs(red - green) > 1e-9 || Math.abs(red - blue) > 1e-9 ||
                                         Math.abs(red - alpha) > 1e-9
    // Frozen while the values are being set (the channels change one after the other)
    property bool editing: false
    property bool frozenSplit: false
    readonly property bool split: editing ? frozenSplit : (!linkable || splitChecked || valuesDiffer)

    readonly property var linkedRange: {
        var child = channelAttribute("r")
        return child && child.desc.range ? child.desc.range : [0, 1, 0.01]
    }

    readonly property var channels: ["r", "g", "b", "a"]
    readonly property real red: channelValue("r")
    readonly property real green: channelValue("g")
    readonly property real blue: channelValue("b")
    readonly property real alpha: channelValue("a")

    spacing: 2

    function channelAttribute(name) {
        return root.attribute.value.get(name)
    }

    function channelValue(name) {
        var child = channelAttribute(name)
        return child ? child.value : 0
    }

    function setAll(value) {
        value = Number(value)
        if (!isFinite(value) || (!valuesDiffer && Math.abs(value - red) < 1e-12))
            return
        frozenSplit = split
        editing = true
        _currentScene.setRgbaAttribute(root.attribute, value, value, value, value)
        editing = false
    }

    function setChannel(channel, value) {
        value = Number(value)
        if (channel && isFinite(value) && Math.abs(value - channel.value) > 1e-12)
            _currentScene.setAttribute(channel, value)
    }

    function setSplit(split) {
        if (!split && valuesDiffer)
            _currentScene.setRgbaAttribute(root.attribute, red, red, red, red)
        _currentScene.setRgbaSplit(root.attribute, split)
        splitChecked = split
    }

    // Linear to sRGB, for the swatch
    function toDisplay(value) {
        var v = Math.max(0, Math.min(1, value))
        return v <= 0.0031308 ? 12.92 * v : 1.055 * Math.pow(v, 1 / 2.4) - 0.055
    }

    // Linked: a single value for the 4 channels
    RowLayout {
        visible: !root.split
        Layout.fillWidth: true
        spacing: 4

        SliderField {
            id: linkedField
            Layout.fillWidth: true
            checked: root.red
            type: "FloatParam"
            length: root.linkedRange.length
            start: root.linkedRange[0]
            end: root.linkedRange[1]
            step: root.linkedRange[2]
            editable: root.editable
            // A hidden field never writes (e.g. when it loses the focus after a split)
            onEditingFinished: (hasExprError, evaluatedValue, text, displayValue) => {
                if (!hasExprError && linkedField.visible)
                    root.setAll(evaluatedValue)
            }
            onAccepted: (hasExprError, evaluatedValue, text, displayValue) => {
                if (!hasExprError && linkedField.visible)
                    root.setAll(evaluatedValue)
            }
            onPressedChanged: (pressed, formattedValue) => {
                if (!pressed && linkedField.visible)
                    root.setAll(formattedValue)
            }
        }

        CheckBox {
            enabled: root.editable
            text: "split"
            font.pointSize: 8
            padding: 0
            checked: false
            ToolTip.text: "Check: a value per channel (r, g, b, a)"
            ToolTip.visible: hovered
            onClicked: {
                root.setSplit(true)
                checked = false
            }
        }
    }

    RowLayout {
        visible: root.split
        Layout.fillWidth: true
        spacing: 4

        // Swatch: the color over a checkerboard showing its alpha
        Rectangle {
            Layout.preferredWidth: 30
            Layout.preferredHeight: 18
            radius: 2
            border.color: Qt.rgba(1, 1, 1, 0.25)
            color: "#808080"
            clip: true

            Grid {
                anchors.fill: parent
                anchors.margins: 1
                columns: 5
                Repeater {
                    model: 15
                    Rectangle {
                        width: 6; height: 6
                        color: (Math.floor(index / 5) + index % 5) % 2 ? "#9A9A9A" : "#5A5A5A"
                    }
                }
            }
            Rectangle {
                anchors.fill: parent
                anchors.margins: 1
                radius: 1
                color: Qt.rgba(root.toDisplay(root.red), root.toDisplay(root.green), root.toDisplay(root.blue),
                               Math.max(0.15, Math.min(1, root.alpha)))
            }
            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: root.expanded = !root.expanded
            }
        }

        Label {
            Layout.fillWidth: true
            text: root.red.toFixed(3) + "  " + root.green.toFixed(3) + "  " + root.blue.toFixed(3) + "  " + root.alpha.toFixed(3)
            elide: Text.ElideRight
            font.pointSize: 8
            opacity: 0.8
            MouseArea {
                anchors.fill: parent
                onClicked: root.expanded = !root.expanded
            }
        }

        CheckBox {
            visible: root.linkable
            enabled: root.editable
            text: "split"
            font.pointSize: 8
            padding: 0
            checked: true
            ToolTip.text: "Uncheck: a single value for the 4 channels (= r)"
            ToolTip.visible: hovered
            onClicked: {
                root.setSplit(false)
                checked = Qt.binding(function() { return root.split })
            }
        }

        MaterialToolButton {
            text: root.expanded ? MaterialIcons.expand_less : MaterialIcons.expand_more
            font.pointSize: 10
            padding: 2
            ToolTip.text: root.expanded ? "Hide the channels" : "Edit the channels"
            onClicked: root.expanded = !root.expanded
        }
    }

    // One slider per channel
    Repeater {
        model: root.expanded && root.split ? root.channels : []

        RowLayout {
            id: channelRow
            required property string modelData
            readonly property var channel: root.channelAttribute(modelData)
            readonly property var range: channel && channel.desc.range ? channel.desc.range : [0, 1, 0.01]
            Layout.fillWidth: true
            spacing: 4

            Label {
                text: channelRow.modelData.toUpperCase()
                Layout.preferredWidth: 12
                color: ({"r": "#E57373", "g": "#81C784", "b": "#64B5F6", "a": "#BDBDBD"})[channelRow.modelData]
            }

            SliderField {
                Layout.fillWidth: true
                checked: channelRow.channel ? channelRow.channel.value : 0
                type: "FloatParam"
                length: channelRow.range.length
                start: channelRow.range[0]
                end: channelRow.range[1]
                step: channelRow.range[2]
                editable: root.editable
                onEditingFinished: (hasExprError, evaluatedValue, text, displayValue) => {
                    if (!hasExprError)
                        root.setChannel(channelRow.channel, evaluatedValue)
                }
                onAccepted: (hasExprError, evaluatedValue, text, displayValue) => {
                    if (!hasExprError)
                        root.setChannel(channelRow.channel, evaluatedValue)
                }
                onPressedChanged: (pressed, formattedValue) => {
                    if (!pressed)
                        root.setChannel(channelRow.channel, formattedValue)
                }
            }
        }
    }
}
