import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import MaterialIcons 2.2
import Controls 1.0
import Utils 1.0

FloatingPane {
    id: root

    property color baseColorValue: colorText.text
    property real textureOpacityValue: textureTF.text
    property real kaValue: ambientTF.text
    property real kdValue: diffuseTF.text
    property real ksValue: specularTF.text
    property real shininessValue: shininessTF.text
    property bool displayLightController: true

    function reset () {
        colorText.text = "#333333"
        textureCtrl.value = 1.0
        ambientCtrl.value = 0.0
        diffuseCtrl.value = 1.0
        specularCtrl.value = 0.5
        shininessCtrl.value = 20.0
    }

    anchors.margins: 0
    padding: 5
    radius: 0

    ColumnLayout {
        id: phongLightingParameters
        anchors.fill: parent
        spacing: 5

        // header
        RowLayout {
            // pane title
            Label {
                text: _reconstruction && _reconstruction.activeNodes.get("PhotometricStereo").node ? _reconstruction.activeNodes.get("PhotometricStereo").node.label : ""
                font.bold: true
                Layout.fillWidth: true
            }

            // minimize or maximize button
            MaterialToolButton {
                id: bodyButton
                text: phongLightingToolbarBody.visible ? MaterialIcons.arrow_drop_down : MaterialIcons.arrow_drop_up
                font.pointSize: 10
                ToolTip.text: phongLightingToolbarBody.visible ? "Minimize" : "Maximize"
                onClicked: { phongLightingToolbarBody.visible = !phongLightingToolbarBody.visible }
            }

            // reset button
            MaterialToolButton {
                id: resetButton
                text: MaterialIcons.refresh
                font.pointSize: 10
                ToolTip.text: "Reset"
                onClicked: reset()
            }

            // settings menu
            MaterialToolButton {
                text: MaterialIcons.settings
                font.pointSize: 10
                onClicked: settingsMenu.popup(width, 0)
                Menu {
                    id: settingsMenu
                    padding: 4
                    implicitWidth: 250

                    RowLayout {
                        Label {
                            text: "Display Directional Light Contoller:"
                        }
                        CheckBox {
                            id: displayLightControllerCB
                            ToolTip.text: "Hides directional light controller."
                            ToolTip.visible: hovered
                            Layout.fillHeight: true
                            Layout.alignment: Qt.AlignRight
                            checked: root.displayLightController
                            onClicked: root.displayLightController = displayLightControllerCB.checked
                        }
                    }
                }
            }
        }
        
        // body
        GridLayout {
            id: phongLightingToolbarBody
            columns: 3
            rowSpacing: 2
            columnSpacing: 8

            // base color
            Label {
                text: "Base Color"
            }
            Rectangle {
                height: colorText.height * 0.8
                color: colorText.text
                Layout.alignment: Qt.AlignVCenter | Qt.AlignRight
                Layout.preferredWidth: textMetricsNormValue.width

                MouseArea {
                    anchors.fill: parent
                    onClicked: colorDialog.open()
                }
            }
            TextField {
                id: colorText
                text: "#333333"
                selectByMouse: true
                Layout.alignment: Qt.AlignLeft
                Layout.fillWidth: true 
            }
            ColorDialog {
                id: colorDialog
                title: "Please choose a color"
                options: ColorDialog.NoEyeDropperButton 
                selectedColor: colorText.text
                onAccepted: {
                    colorText.text = selectedColor
                    colorText.editingFinished() // artificially trigger change of attribute value
                    close()
                }
                onRejected: close()
            }

            // texture opacity
            Label {
                text: "Texture"
            }
            TextField {
                id: textureTF
                text: textureCtrl.value.toFixed(2)
                selectByMouse: true
                horizontalAlignment: TextInput.AlignRight
                validator: doubleNormalizedValidator
                onEditingFinished: { textureCtrl.value = textureTF.text }
                ToolTip.text: "Texture Opacity."
                ToolTip.visible: hovered
                Layout.preferredWidth: textMetricsNormValue.width
            }
            Slider {
                id: textureCtrl
                from: 0.0
                to: 1.0
                value: 1.0
                stepSize: 0.01
                Layout.fillWidth: true                                       
            }

            // diffuse (kd)
            Label {
                text: "Diffuse"
            }
            TextField {
                id: diffuseTF
                text: diffuseCtrl.value.toFixed(2)
                selectByMouse: true
                horizontalAlignment: TextInput.AlignRight
                validator: doubleNormalizedValidator
                onEditingFinished: { diffuseCtrl.value = diffuseTF.text }
                ToolTip.text: "Diffuse reflection (kd)."
                ToolTip.visible: hovered
                Layout.preferredWidth: textMetricsNormValue.width
            }
            Slider {
                id: diffuseCtrl
                from: 0.0
                to: 1.0
                value: 1.0
                stepSize: 0.01
                Layout.fillWidth: true                                       
            }

            // ambient (ka)
            Label {
                text: "Ambient"
            }
            TextField {
                id: ambientTF
                text: ambientCtrl.value.toFixed(2)
                selectByMouse: true
                horizontalAlignment: TextInput.AlignRight
                validator: doubleNormalizedValidator
                onEditingFinished: { ambientCtrl.value = ambientTF.text }
                ToolTip.text: "Ambient reflection (ka)."
                ToolTip.visible: hovered
                Layout.preferredWidth: textMetricsNormValue.width
            }
            Slider {
                id: ambientCtrl
                from: 0.0
                to: 1.0
                value: 0.0
                stepSize: 0.01 
                Layout.fillWidth: true                                 
            }

            // specular (ks)
            Label {
                text: "Specular"
            }
            TextField {
                id: specularTF
                text: specularCtrl.value.toFixed(2)
                selectByMouse: true
                horizontalAlignment: TextInput.AlignRight
                validator: doubleNormalizedValidator
                onEditingFinished: { specularCtrl.value = specularTF.text }
                ToolTip.text: "Specular reflection (ks)."
                ToolTip.visible: hovered
                Layout.preferredWidth: textMetricsNormValue.width
            }
            Slider {
                id: specularCtrl
                from: 0.0
                to: 1.0
                value: 0.5
                stepSize: 0.01
                Layout.fillWidth: true                                         
            }

            // shininess
            Label {
                text: "Shininess"
            }
            TextField {
                id: shininessTF
                text: shininessCtrl.value
                selectByMouse: true
                horizontalAlignment: TextInput.AlignRight
                validator: intShininessValidator
                onEditingFinished: { shininessCtrl.value = shininessTF.text }
                ToolTip.text: "Shininess constant."
                ToolTip.visible: hovered
                Layout.preferredWidth: textMetricsNormValue.width
            }
            Slider {
                id: shininessCtrl
                from: 1
                to: 128
                value: 20
                stepSize: 1
                Layout.fillWidth: true                                         
            }
        }
    }

    DoubleValidator {
        id: doubleNormalizedValidator
        locale: 'C' // use '.' decimal separator disregarding of the system locale
        bottom: 0.0
        top: 1.0
    }

    IntValidator {
        id: intShininessValidator
        bottom: 1
        top: 128
    }

    TextMetrics {
        id: textMetricsNormValue
        font: ambientTF.font
        text: "1.2345" 
    }
}