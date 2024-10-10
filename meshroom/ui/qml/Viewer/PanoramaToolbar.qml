import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Controls 1.0
import MaterialIcons 2.2
import Utils 1.0

FloatingPane {
    id: root
    anchors.margins: 0
    padding: 5
    radius: 0

    property bool enableEdit: enablePanoramaEdit.checked
    property bool enableHover: enableHover.checked
    property bool displayGrid: displayGrid.checked

    property int downscaleValue: downscaleSpinBox.value
    property int downscaleDefaultValue: 4

    property int subdivisionsDefaultValue: 24
    property int subdivisionsValue: subdivisionsCtrl.value

    property int mouseSpeed: speedSpinBox.value

    background: Rectangle { color: root.palette.window }

    function updateDownscaleValue(level) {
        downscaleSpinBox.value = level
    }

    DoubleValidator {
        id: doubleValidator
        locale: 'C'  // Use '.' decimal separator disregarding of the system locale
    }

    RowLayout {
        id: toolLayout
        anchors.fill: parent

        MaterialToolButton {
            id: enablePanoramaEdit
            ToolTip.text: "Enable Panorama edition"
            text: MaterialIcons.open_with
            font.pointSize: 14
            padding: 5
            Layout.minimumWidth: 0
            checkable: true
            checked: true
        }
        MaterialToolButton {
            id: enableHover
            ToolTip.text: "Enable hovering highlight"
            text: MaterialIcons.highlight
            font.pointSize: 14
            padding: 5
            Layout.minimumWidth: 0
            checkable: true
            checked: true
        }
        MaterialToolButton {
            id: displayGrid
            ToolTip.text: "Display grid"
            text: MaterialIcons.grid_on
            font.pointSize: 14
            padding: 5
            Layout.minimumWidth: 0
            checkable: true
            checked: true
        }
        RowLayout {
            spacing: 5

            ToolButton {
                text: "Subdivisions"

                ToolTip.visible: ToolTip.text && hovered
                ToolTip.delay: 100
                ToolTip.text: "Reset Subdivisions"

                onClicked: {
                    subdivisionsCtrl.value = subdivisionsDefaultValue
                }
            }
            TextField {
                id: subdivisionsLabel

                ToolTip.visible: ToolTip.text && hovered
                ToolTip.delay: 100
                ToolTip.text: "subdivisions"

                text: subdivisionsValue.toFixed(1)
                Layout.preferredWidth: textMetrics_subdivisionsValue.width
                selectByMouse: true
                validator: doubleValidator
                onAccepted: {
                    subdivisionsCtrl.value = Number(subdivisionsLabel.text)
                }
            }
            Slider {
                id: subdivisionsCtrl
                Layout.fillWidth: false
                from: 2
                to: 72
                value: subdivisionsDefaultValue
                stepSize: 2
            }
        }
        Rectangle{
            color: root.palette.window
            Layout.fillWidth: true
        }
        RowLayout{
            ToolButton {
                text: "Edit Speed"

                ToolTip.visible: ToolTip.text && hovered
                ToolTip.delay: 100
                ToolTip.text: "Reset the mouse multiplier"

                onClicked: {
                    speedSpinBox.value = 1
                }
            }
            SpinBox {
                id: speedSpinBox
                from: 1
                value: 1
                to: 10
                stepSize: 1
                Layout.fillWidth: false
                Layout.maximumWidth: 50

                validator: DoubleValidator {
                    bottom: Math.min(speedSpinBox.from, speedSpinBox.to)
                    top: Math.max(speedSpinBox.from, speedSpinBox.to)
                }

                textFromValue: function(value, locale) {
                    return "x" + value.toString()

                }
            }
        }
        RowLayout{
            ToolButton {
                text: "Downscale"

                ToolTip.visible: ToolTip.text && hovered
                ToolTip.delay: 100
                ToolTip.text: "Reset the downscale"

                onClicked: {
                    downscaleSpinBox.value = downscaleDefaultValue
                }
            }
            SpinBox {
                id: downscaleSpinBox
                from: 0
                value: downscaleDefaultValue
                to: 5
                stepSize: 1
                Layout.fillWidth: false
                Layout.maximumWidth: 50

                validator: DoubleValidator {
                    bottom: Math.min(downscaleSpinBox.from, downscaleSpinBox.to)
                    top: Math.max(downscaleSpinBox.from, downscaleSpinBox.to)
                }

                textFromValue: function(value, locale) {
                    if (value === 0){
                        return 1
                    } else {
                        return "1/" + Math.pow(2, value).toString()
                    }
                }
            }
        }
    }

    TextMetrics {
        id: textMetrics_subdivisionsValue
        font: subdivisionsLabel.font
        text: "100.00"
    }
}
