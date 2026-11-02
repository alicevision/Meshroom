import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

/**
 * Labelled ComboBox editing the integer (enum index) property @p propertyName of @p target.
 */
RowLayout {
    id: root

    property var target: null
    property string propertyName: ""
    property string label: ""
    property int labelWidth: 42
    property alias model: comboBox.model

    readonly property bool hasProperty: target !== null && target[propertyName] !== undefined

    spacing: 4

    Label {
        text: root.label
        color: palette.text
        Layout.preferredWidth: root.labelWidth
    }

    ComboBox {
        id: comboBox
        enabled: root.hasProperty
        currentIndex: root.hasProperty ? root.target[root.propertyName] : 0
        onActivated: (index) => root.target[root.propertyName] = index
    }
}
