import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

RowLayout {
    id: root
    required property var value
    property bool editable
    signal editingFinished(var text)
    signal accepted(var text)
    signal destruction(bool activeFocus, var text)
    signal pressedChanged(bool pressed, var formattedValue)

    TextField {
        id: textField
        implicitWidth: 100
        enabled: root.editable
        // Cast value to string to avoid intrusive scientific notations on numbers
        property string displayValue: String(slider.pressed ? slider.formattedValue : root.value)
        text: displayValue
        selectByMouse: true
        validator: DoubleValidator {
            locale: 'C'  // Use '.' decimal separator disregarding the system locale
        }
        onEditingFinished: root.editingFinished(text)
        onAccepted: root.accepted(text)
        Component.onDestruction: root.destruction(activeFocus, text)
        background: Rectangle {
            radius: 2
            border.width: textField.activeFocus ? 2 : 1
            border.color: textField.activeFocus ? palette.highlight : palette.mid
            color: Qt.darker(palette.window, 1.2)
        }

        WheelHandler {
            id: textFieldWheelHandler
            enabled: root.editable && textField.activeFocus
            onWheel: (event) => {
                var step = (event.modifiers & Qt.ShiftModifier) ? 0.1 : 0.01
                var delta = (event.angleDelta.y > 0 ? step : -step)
                var newVal = Math.max(0, Math.min(1, Number(root.value) + delta))
                var text = newVal.toFixed(2)
                root.editingFinished(text)
                root.accepted(text)
            }
        }
    }

    Rectangle {
        height: slider.height
        width: height
        color: Qt.hsla(slider.pressed ? slider.formattedValue : root.value, 1, 0.5, 1)
    }

    Slider {
        id: slider
        Layout.fillWidth: true
        readonly property int stepDecimalCount: 2
        readonly property real formattedValue: value.toFixed(stepDecimalCount)
        enabled: root.editable
        focusPolicy: Qt.StrongFocus
        value: root.value
        from: 0
        to: 1
        stepSize: 0.01
        snapMode: Slider.SnapAlways
        onPressedChanged: root.pressedChanged(pressed, formattedValue)
        background: ShaderEffect {
            width: slider.availableWidth
            height: slider.availableHeight
            blending: false
            fragmentShader: "qrc:/shaders/AttributeItemDelegate.frag.qsb"
        }
    }
}