import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Controls 1.0

FloatingPane {
    id: root
    anchors.margins: 0
    padding: 5
    radius: 0

    property real gainDefaultValue: 1.0
    property real gammaDefaultValue: 1.0

    function resetDefaultValues() {
        gainCtrl.value = root.gainDefaultValue
        gammaCtrl.value = root.gammaDefaultValue
    }

    property real slidersPowerValue: 4.0
    property real gainValue: Math.pow(gainCtrl.value, slidersPowerValue)
    property real gammaValue: Math.pow(gammaCtrl.value, slidersPowerValue)
    property alias channelModeValue: channelsCtrl.value
    property variant colorRGBA: null

    property bool colorPickerVisible: true

    background: Rectangle { color: root.palette.window }

    DoubleValidator {
        id: doubleValidator
        locale: 'C'  // Use '.' decimal separator disregarding of the system locale
    }

    RowLayout {
        id: toolLayout
        anchors.fill: parent

        // Channel mode
        ComboBox {
            id: channelsCtrl

            // Set min size to 4 characters + one margin for the combobox
            Layout.minimumWidth: 5.0 * Qt.application.font.pixelSize
            Layout.preferredWidth: Layout.minimumWidth
            flat: true

            property var channels: ["rgba", "rgb", "r", "g", "b","a"]
            property string value: channels[currentIndex]

            onValueChanged: {
                currentIndex = channels.indexOf(value)
            }

            model: channels
        }

        // Gain slider
        RowLayout {
            spacing: 5

            ToolButton {
                text: "Gain"

                ToolTip.visible: ToolTip.text && hovered
                ToolTip.delay: 100
                ToolTip.text: "Reset Gain"

                onClicked: {
                    gainCtrl.value = gainDefaultValue
                }
            }
            TextField {
                id: gainLabel

                ToolTip.visible: ToolTip.text && hovered
                ToolTip.delay: 100
                ToolTip.text: "Color Gain (in linear colorspace)"

                text: gainValue.toFixed(2)
                Layout.preferredWidth: textMetrics_gainValue.width
                selectByMouse: true
                validator: doubleValidator
                onAccepted: {
                    gainCtrl.value = Math.pow(Number(gainLabel.text), 1.0 / slidersPowerValue)
                }
            }
            Slider {
                id: gainCtrl
                Layout.fillWidth: true
                from: 0.01
                to: 2
                value: gainDefaultValue
                stepSize: 0.01
            }
        }

        // Gamma slider
        RowLayout {
            spacing: 5

            ToolButton {
                text: "γ"

                ToolTip.visible: ToolTip.text && hovered
                ToolTip.delay: 100
                ToolTip.text: "Reset Gamma"

                onClicked: {
                    gammaCtrl.value = gammaDefaultValue;
                }
            }
            TextField {
                id: gammaLabel

                ToolTip.visible: ToolTip.text && hovered
                ToolTip.delay: 100
                ToolTip.text: "Apply Gamma (after Gain and in linear colorspace)"

                text: gammaValue.toFixed(2)
                Layout.preferredWidth: textMetrics_gainValue.width
                selectByMouse: true
                validator: doubleValidator
                onAccepted: {
                    gammaCtrl.value = Math.pow(Number(gammaLabel.text), 1.0 / slidersPowerValue)
                }
            }
            Slider {
                id: gammaCtrl
                Layout.fillWidth: true
                from: 0.01
                to: 2
                value: gammaDefaultValue
                stepSize: 0.01
            }
        }

        Rectangle {
            visible: colorPickerVisible
            Layout.preferredWidth: 20
            implicitWidth: 20
            implicitHeight: parent.height
            color: root.colorRGBA ? Qt.rgba(red.value_gamma, green.value_gamma, blue.value_gamma, 1.0) : "black"
        }

        // RGBA colors
        RowLayout {
            spacing: 1
            visible: colorPickerVisible
            TextField {
                id: red
                property real value: root.colorRGBA ? root.colorRGBA.x : 0.0
                property real value_gamma: Math.pow(value, 1.0 / 2.2)
                text: root.colorRGBA ? value.toFixed(6) : "--"

                Layout.preferredWidth: textMetrics_colorValue.width
                selectByMouse: true
                validator: doubleValidator
                horizontalAlignment: TextInput.AlignLeft
                readOnly: true
                // autoScroll: When the text is too long, display the left part
                // (with the most important values and cut the floating point details)
                autoScroll: false

                Rectangle {
                    anchors.verticalCenter: parent.bottom
                    width: parent.width
                    height: 3
                    color: Qt.rgba(red.value_gamma, 0.0, 0.0, 1.0)
                }
            }
            TextField {
                id: green
                property real value: root.colorRGBA ? root.colorRGBA.y : 0.0
                property real value_gamma: Math.pow(value, 1.0/2.2)
                text: root.colorRGBA ? value.toFixed(6) : "--"
                
                Layout.preferredWidth: textMetrics_colorValue.width
                selectByMouse: true
                validator: doubleValidator
                horizontalAlignment: TextInput.AlignLeft
                readOnly: true
                // autoScroll: When the text is too long, display the left part
                // (with the most important values and cut the floating point details)
                autoScroll: false

                Rectangle {
                    anchors.verticalCenter: parent.bottom
                    width: parent.width
                    height: 3
                    color: Qt.rgba(0.0, green.value_gamma, 0.0, 1.0)
                }
            }
            TextField {
                id: blue
                property real value: root.colorRGBA ? root.colorRGBA.z : 0.0
                property real value_gamma: Math.pow(value, 1.0 / 2.2)
                text: root.colorRGBA ? value.toFixed(6) : "--"
                
                Layout.preferredWidth: textMetrics_colorValue.width
                selectByMouse: true
                validator: doubleValidator
                horizontalAlignment: TextInput.AlignLeft
                readOnly: true
                // autoScroll: When the text is too long, display the left part
                // (with the most important values and cut the floating point details)
                autoScroll: false

                Rectangle {
                    anchors.verticalCenter: parent.bottom
                    width: parent.width
                    height: 3
                    color: Qt.rgba(0.0, 0.0, blue.value_gamma, 1.0)
                }
            }
            TextField {
                id: alpha
                property real value: root.colorRGBA ? root.colorRGBA.w : 0.0
                property real value_gamma: Math.pow(value, 1.0 / 2.2)
                text: root.colorRGBA ? value.toFixed(6) : "--"
                
                Layout.preferredWidth: textMetrics_colorValue.width
                selectByMouse: true
                validator: doubleValidator
                horizontalAlignment: TextInput.AlignLeft
                readOnly: true
                // autoScroll: When the text is too long, display the left part
                // (with the most important values and cut the floating point details)
                autoScroll: false

                Rectangle {
                    anchors.verticalCenter: parent.bottom
                    width: parent.width
                    height: 3
                    color: Qt.rgba(alpha.value_gamma, alpha.value_gamma, alpha.value_gamma, 1.0)
                }
            }
        }
    }
    TextMetrics {
        id: textMetrics_colorValue
        font: red.font
        text: "1.2345"  // Use one more than expected to get the correct value (probably needed due to TextField margin)
    }
    TextMetrics {
        id: textMetrics_gainValue
        font: gainLabel.font
        text: "1.2345"
    }
}
