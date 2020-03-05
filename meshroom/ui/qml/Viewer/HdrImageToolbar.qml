import QtQuick 2.11
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3
import MaterialIcons 2.2
import Controls 1.0

FloatingPane {
    id: root
    anchors.margins: 0
    padding: 5
    radius: 0

    property real gammaDefaultValue: 1
    property real offsetDefaultValue: 0
    property real gammaValue: gammaCtrl.value
    property real offsetValue: offsetCtrl.value
    property string channelModeValue: channelsCtrl.value
    property variant colorRGBA: null

    background: Rectangle { color: root.palette.window }

    DoubleValidator {
        id: doubleValidator
        locale: 'C' // use '.' decimal separator disregarding of the system locale
    }

    RowLayout {
        id: toolLayout
        // anchors.verticalCenter: parent
        anchors.fill: parent

        // channel mode
        ComboBox {
            id: channelsCtrl

            // set min size to 4 characters + one margin for the combobox
            Layout.minimumWidth: 5.0 * Qt.application.font.pixelSize
            Layout.preferredWidth: Layout.minimumWidth
            flat: true

            property var channels: ["rgba", "rgb", "r", "g", "b","a"]
            property string value: channels[currentIndex]

            model: channels
        }

        // offset slider
        RowLayout {
            spacing: 5

            ToolButton {
                text: "Gain"

                ToolTip.visible: ToolTip.text && hovered
                ToolTip.delay: 100
                ToolTip.text: "Reset Gain"

                onClicked: {
                    offsetCtrl.value = offsetDefaultValue;
                }
            }
            TextField {
                id: offsetLabel

                ToolTip.visible: ToolTip.text && hovered
                ToolTip.delay: 100
                ToolTip.text: "Color Gain (in linear colorspace)"

                text: offsetValue.toFixed(2)
                Layout.preferredWidth: textMetrics_offsetValue.width
                selectByMouse: true
                validator: doubleValidator
                onAccepted: {
                    offsetCtrl.value = Number(offsetLabel.text)
                }
            }
            Slider {
                id: offsetCtrl
                Layout.fillWidth: true
                from: -1
                to: 1
                value: 0
                stepSize: 0.01
            }
        }

        // gamma slider
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
                Layout.preferredWidth: textMetrics_offsetValue.width
                selectByMouse: true
                validator: doubleValidator
                onAccepted: {
                    gammaCtrl.value = Number(offsetLabel.text)
                }
            }
            Slider {
                id: gammaCtrl
                Layout.fillWidth: true
                from: 0.01
                to: 4
                value: 1
                stepSize: 0.01
            }
        }

        Rectangle {
            Layout.preferredWidth: 20
            implicitWidth: 20
            implicitHeight: parent.height
            color: root.colorRGBA ? Qt.rgba(red.value_gamma, green.value_gamma, blue.value_gamma, 1.0) : "black"
        }

        // gamma slider
        RowLayout {
            spacing: 1
            TextField {
                id: red
                property real value: root.colorRGBA ? root.colorRGBA.x : 0.0
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
                    color: Qt.rgba(0.0, 0.0, blue.value_gamma, 1.0)
                }
            }
            TextField {
                id: alpha
                property real value: root.colorRGBA ? root.colorRGBA.w : 0.0
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
                    color: Qt.rgba(alpha.value_gamma, alpha.value_gamma, alpha.value_gamma, 1.0)
                }
            }
        }
    }
    TextMetrics {
        id: textMetrics_colorValue
        font: red.font
        text: "1.2345" // use one more than expected to get the correct value (probably needed due to TextField margin)
    }
    TextMetrics {
        id: textMetrics_offsetValue
        font: offsetLabel.font
        text: "-10.01"
    }
}
