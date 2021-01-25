import QtQuick 2.11
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3
import MaterialIcons 2.2
import Controls 1.0
import Utils 1.0

FloatingPane {
    id: root
    anchors.margins: 0
    padding: 5
    radius: 0

    property bool enableEdit: enablePanoramaEdit.checked
    property bool enableHover: enableHover.checked

    property int downscaleDefaultValue: 2

    background: Rectangle { color: root.palette.window }

    DoubleValidator {
        id: doubleValidator
        locale: 'C' // use '.' decimal separator disregarding of the system locale
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
        //Fill rectangle to have a better UI
        Rectangle {
            color: root.palette.window
            Layout.fillWidth: true
        }
        RowLayout{
            ToolButton {
                text: "Downscale"

                ToolTip.visible: ToolTip.text && hovered
                ToolTip.delay: 100
                ToolTip.text: "Reset the downscale"

                onClicked: {
                    downscaleSpinBox.value = downscaleDefaultValue;
                }
            }
            SpinBox {
                id: downscaleSpinBox
                from: 0
                value: 2
                to: 3
                stepSize: 1
                Layout.fillWidth: false


                validator: DoubleValidator {
                    bottom: Math.min(downscaleSpinBox.from, downscaleSpinBox.to)
                    top:  Math.max(downscaleSpinBox.from, downscaleSpinBox.to)
                }

                textFromValue: function(value, locale) {
                    if(value === 0){
                        return 1
                    }
                    else{
                        return "1/" + Math.pow(2,value).toString()
                    }

                }
            }
        }

    }

}
