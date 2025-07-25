import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Shapes
import MaterialIcons 2.2
import Utils 1.0

/**
* Directional Light Pane
*
* @biref A small pane to control a directional light with a 2d ball controller.
*
* @param lightYawValue - directional light yaw (degrees)
* @param lightPitchValue - directional light pitch (degrees)
*/
FloatingPane {
    id: root

    // yaw and pitch properties
    property double lightYawValue: 0
    property double lightPitchValue: 0

    // 2d controller display size properties
    readonly property real controllerSize: 80
    readonly property real controllerRadius: controllerSize * 0.5

    function reset() {
        lightYawValue = 0;
        lightPitchValue = 0;
    }

    // update 2d controller if yaw value changed
    onLightYawValueChanged: { lightBallController.update() }

    // update 2d controller if pitch value changed
    onLightPitchValueChanged: { lightBallController.update() }

    // pane properties
    anchors.margins: 0
    padding: 5

    ColumnLayout {
        anchors.fill: parent
        spacing: 5

        // header
        RowLayout {
            // pane title
            Label {
                text: "Directional Light"
                font.bold: true
                Layout.fillWidth: true
            }

            // minimize or maximize button
            MaterialToolButton {
                id: bodyButton
                text: lightPaneBody.visible ? MaterialIcons.arrow_drop_down : MaterialIcons.arrow_drop_up
                font.pointSize: 10
                ToolTip.text: lightPaneBody.visible ? "Minimize" : "Maximize"
                onClicked: { lightPaneBody.visible = !lightPaneBody.visible }
            }

            // reset button
            MaterialToolButton {
                id: resetButton
                text: MaterialIcons.refresh
                font.pointSize: 10
                ToolTip.text: "Reset"
                onClicked: reset()
            }
        }

        // body
        RowLayout {
            id: lightPaneBody
            spacing: 10

            // light parameters
            GridLayout {
                columns: 3
                rowSpacing: 2
                columnSpacing: 8
                Layout.alignment: Qt.AlignBottom

                // light yaw
                Label {
                    text: "Yaw"
                }
                TextField {
                    id: lightYawTF
                    text: lightYawValue.toFixed(2)
                    selectByMouse: true
                    horizontalAlignment: TextInput.AlignRight
                    validator: doubleDegreeValidator
                    onEditingFinished: { lightYawValue = lightYawTF.text }
                    ToolTip.text: "Light yaw (degrees)."
                    ToolTip.visible: hovered
                    Layout.preferredWidth: textMetricsDegreeValue.width
                }
                Label {
                    text: "°"
                }

                // light pitch
                Label {
                    text: "Pitch"
                }
                TextField {
                    id: lightPitchTF
                    text: lightPitchValue.toFixed(2)
                    selectByMouse: true
                    horizontalAlignment: TextInput.AlignRight
                    validator: doubleDegreeValidator
                    onEditingFinished: { lightPitchValue = lightPitchTF.text }
                    ToolTip.text: "Light pitch (degrees)."
                    ToolTip.visible: hovered
                    Layout.preferredWidth: textMetricsDegreeValue.width
                }
                Label {
                    text: "°"
                }
            }

            // directional light ball controller
            Rectangle {
                id: lightBallController
                anchors.margins: 0
                width: controllerSize
                height: controllerSize
                radius: 180 // circle
                color: "#FF000000"
                Layout.rightMargin: 5
                Layout.leftMargin: 5
                Layout.bottomMargin: 5

                function update() {
                    // get point from light yaw and pitch
                    var y = (lightPitchValue / 90 * controllerRadius)
                    var xMax = Math.sqrt(controllerRadius * controllerRadius - y * y) // get sphere maximum x coordinate
                    var x = (lightYawValue / 90 * xMax)

                    // get angle and distance
                    var angleRad = Math.atan2(y, x)
                    var distance = Math.sqrt(x * x + y * y)

                    // avoid controller overflow  
                    if(distance > controllerRadius)
                    {
                        x = controllerRadius * Math.cos(angleRad)
                        y = controllerRadius * Math.sin(angleRad)
                    }

                    // update light point
                    lightPoint.x = lightPoint.startOffset + x
                    lightPoint.y = lightPoint.startOffset + y
                }

               
                // light ball controller shapes
                Shape {
                    anchors.centerIn: parent
                    width: parent.width
                    height: parent.height

                    // ball shape
                    ShapePath {
                        strokeWidth: 0

                        // shade gradient
                        fillGradient: RadialGradient {
                            centerX: lightPoint.x + lightPoint.radius
                            centerY: lightPoint.y + lightPoint.radius
                            centerRadius: controllerSize
                            focalX: (lightPoint.x - lightPoint.startOffset) * 0.75 + lightPoint.startOffset + lightPoint.radius
                            focalY: (lightPoint.y - lightPoint.startOffset) * 0.75 + lightPoint.startOffset + lightPoint.radius
                            focalRadius: 2 
                            GradientStop { position: 0.00; color: "#FFCCCCCC" }
                            GradientStop { position: 0.05; color: "#FFAAAAAA" }
                            GradientStop { position: 0.50; color: "#FF0C0C0C" }
                        }

                        // ball circle path
                        PathRectangle {
                            x: 0
                            y: 0
                            width: controllerSize
                            height: controllerSize
                            radius: controllerSize * 0.5 // circle shape
                        }
                    }

                    // light point shape
                    ShapePath {
                        strokeWidth: 0

                        // glow gradient
                        fillGradient: RadialGradient {
                            centerX: lightPoint.x + centerRadius
                            centerY: lightPoint.y + centerRadius
                            centerRadius: lightPoint.radius
                            focalX: centerX
                            focalY: centerY
                            GradientStop { position: 0.4; color: "#FFFFFFFF" }
                            GradientStop { position: 0.75; color: "#33FFFFFF" }
                            GradientStop { position: 1.0; color: "#00FFFFFF" }
                        }

                        // point circle path
                        PathRectangle {
                            id: lightPoint
                            readonly property double startOffset : (lightBallController.width - width) * 0.5 
                            x: startOffset
                            y: startOffset
                            width: controllerRadius * 0.4
                            height: width
                            radius: width * 0.5  // circle shape
                        }
                    }
                }

                MouseArea {
                    id: lightMouseArea
                    anchors.centerIn: parent
                    anchors.fill: parent

                    onPositionChanged: {
                        // get coordinates from center
                        var x = mouseX - controllerRadius
                        var y = mouseY - controllerRadius

                        // get distance to center
                        var distance = Math.sqrt(x * x + y * y)

                        // avoid controller overflow  
                        if(distance > controllerRadius)
                        {
                            var angleRad = Math.atan2(y, x)
                            x = controllerRadius * Math.cos(angleRad)
                            y = controllerRadius * Math.sin(angleRad)
                        }

                        // get sphere maximum x coordinate
                        var xMax = Math.sqrt(controllerRadius * controllerRadius - y * y)

                        // update light yaw and pitch
                        lightYawValue = (xMax > 0) ? ((x / xMax) * 90) : 0 // between -90 and 90 degrees
                        lightPitchValue = (y / controllerRadius) * 90      // between -90 and 90 degrees
                    }
                }
            }
        }
    }

    DoubleValidator {
        id: doubleDegreeValidator
        locale: 'C' // use '.' decimal separator disregarding of the system locale
        bottom: -90.0
        top: 90.0
    }

    TextMetrics {
        id: textMetricsDegreeValue
        font: lightYawTF.font
        text: "12.3456" 
    }
}