import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import MaterialIcons
import Controls

/**
 * A combobox-type control with a single current `value` and a list of possible `values`.
 * Provides filtering capabilities and support for custom values (i.e: `value` not in `values`).
 */
RowLayout {
    id: root

    required property var value
    required property var values

    signal editingFinished(var value)

    Item {
        Layout.fillWidth: true
        implicitWidth: comboBox.implicitWidth
        implicitHeight: comboBox.implicitHeight

        FilterComboBox {
            id: comboBox
            anchors.fill: parent
            sourceModel: root.values
            inputValue: root.value
            onEditingFinished: value => root.editingFinished(value)
        }

        Rectangle {
            anchors.fill: comboBox
            color: "transparent"
            radius: 2
            border.width: comboBox.activeFocus ? 2 : 0
            border.color: comboBox.palette.highlight
            z: 10
        }
    }

    MaterialLabel {
        visible: !comboBox.validValue
        text: MaterialIcons.warning
        ToolTip.text: "Custom value detected"
    }
}