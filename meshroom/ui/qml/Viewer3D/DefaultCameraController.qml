import QtQuick 2.15
import Qt3D.Core 2.15
import Qt3D.Render 2.15
import Qt3D.Input 2.15
import Qt3D.Logic 2.15
import QtQml 2.2

import Meshroom.Helpers 1.0

Entity {
    id: root

    property Camera camera
    property real translateSpeed: 75.0
    property real tiltSpeed: 500.0
    property real panSpeed: 500.0
    readonly property bool moving: actionLMB.active
    readonly property bool panning: (keyboardHandler._pressed && actionLMB.active && actionShift.active) || actionMMB.active
    readonly property bool zooming: keyboardHandler._pressed && actionRMB.active && actionAlt.active
    property alias focus: keyboardHandler.focus
    readonly property bool pickingActive: actionControl.active && keyboardHandler._pressed
    property alias rotationSpeed: trackball.rotationSpeed
    property alias windowSize: trackball.windowSize
    property alias trackballSize: trackball.trackballSize

    property bool loseMouseFocus: false // Must be changed by other entities when they want to take mouse focus

    readonly property alias pressed: mouseHandler._pressed
    signal mousePressed(var mouse)
    signal mouseReleased(var mouse, var moved)
    signal mouseClicked(var mouse)
    signal mouseWheeled(var wheel)
    signal mouseDoubleClicked(var mouse)

    KeyboardDevice { id: keyboardSourceDevice }
    MouseDevice { id: mouseSourceDevice }

    TrackballController {
        id: trackball
        camera: root.camera
    }

    MouseHandler {
        id: mouseHandler
        property bool _pressed
        property point lastPosition
        property point currentPosition
        property bool hasMoved
        sourceDevice: loseMouseFocus ? null : mouseSourceDevice
        onPressed: {
            _pressed = true
            currentPosition.x = lastPosition.x = mouse.x
            currentPosition.y = lastPosition.y = mouse.y
            hasMoved = false
            mousePressed(mouse)
        }
        onReleased: {
            _pressed = false
            mouseReleased(mouse, hasMoved)
        }
        onClicked: mouseClicked(mouse)
        onPositionChanged: {
            currentPosition.x = mouse.x
            currentPosition.y = mouse.y

            const dt = 0.02
            var d

            if (panning) { // translate
                d = (root.camera.viewCenter.minus(root.camera.position)).length() * 0.03
                var tx = axisMX.value * root.translateSpeed * d
                var ty = axisMY.value * root.translateSpeed * d
                mouseHandler.hasMoved = true
                root.camera.translate(Qt.vector3d(-tx, -ty, 0).times(dt))
                return
            }
            if (moving){ // trackball rotation
                trackball.rotate(mouseHandler.lastPosition, mouseHandler.currentPosition, dt)
                mouseHandler.lastPosition = mouseHandler.currentPosition
                mouseHandler.hasMoved = true
                return
            }
            if (zooming) { // zoom with alt + RMD
                mouseHandler.hasMoved = true
                d = root.camera.viewCenter.minus(root.camera.position).length() // Distance between camera position and center position
                var zoomPower = 0.2
                var tz = axisMX.value * root.translateSpeed * zoomPower // Translation to apply depending on user action (mouse move), bigger absolute value means we'll zoom/dezoom more
                var tzThreshold = 0.001

                // We forbid too big zoom, as it means the distance between camera and center would be too low and we'll have no translation after (due to float representation)
                if (tz >= 0.9 * d)
                    return

                // We forbid too small zoom as it means we are getting very close to center position and next zoom may lead to similar problem as previous cases (no translation), problem occurs only if tz > 0 (when we zoom)
                if (tz > 0 && tz <= tzThreshold)
                    return

                root.camera.translate(Qt.vector3d(0, 0, tz), Camera.DontTranslateViewCenter)
                return
            }
        }

        onDoubleClicked: mouseDoubleClicked(mouse)
        onWheel: {
            var d = root.camera.viewCenter.minus(root.camera.position).length() // Distance between camera position and center position
            var zoomPower = 0.2
            var angleStep = 120 // wheel.angleDelta.y = +- 120 * number of wheel rotations
            var tz = (wheel.angleDelta.y / angleStep) * d * zoomPower // Translation to apply depending on user action (mouse wheel), bigger absolute value means we'll zoom/dezoom more
            var tzThreshold = 0.001

            // We forbid too big zoom, as it means the distance between camera and center would be too low and we'll have no translation after (due to float representation)
            if (tz >= 0.9 * d) {
                return
            }

            // We forbid too small zoom as it means we are getting very close to center position and next zoom may lead to similar problem as previous cases (no translation), problem occurs only if tz > 0 (when we zoom)
            if (tz > 0 && tz <= tzThreshold) {
                return
            }
            root.camera.translate(Qt.vector3d(0, 0, tz), Camera.DontTranslateViewCenter)
        }
    }

    KeyboardHandler {
        id: keyboardHandler
        sourceDevice: keyboardSourceDevice
        property bool _pressed

        // When focus is lost while pressing a key, the corresponding action
        // stays active, even when it's released.
        // Handle this issue manually by keeping an additional _pressed state
        // which is cleared when focus changes (used for 'pickingActive' property).
        onFocusChanged: if (!focus) _pressed = false
        onPressed: _pressed = true
        onReleased: _pressed = false
    }

    LogicalDevice {
        id: cameraControlDevice
        actions: [
            Action {
                id: actionLMB
                inputs: [
                    ActionInput {
                        sourceDevice: mouseSourceDevice
                        buttons: [MouseEvent.LeftButton]
                    }
                ]
            },
            Action {
                id: actionRMB
                inputs: [
                    ActionInput {
                        sourceDevice: mouseSourceDevice
                        buttons: [MouseEvent.RightButton]
                    }
                ]
            },
            Action {
                id: actionMMB
                inputs: [
                    ActionInput {
                        sourceDevice: mouseSourceDevice
                        buttons: [MouseEvent.MiddleButton]
                    }
                ]
            },
            Action {
                id: actionShift
                inputs: [
                    ActionInput {
                        sourceDevice: keyboardSourceDevice
                        buttons: [Qt.Key_Shift]
                    }
                ]
            },
            Action {
                id: actionControl
                inputs: [
                    ActionInput {
                        sourceDevice: keyboardSourceDevice
                        buttons: [Qt.Key_Control]
                    }
                ]
            },
            Action {
                id: actionAlt
                inputs: [
                    ActionInput {
                        sourceDevice: keyboardSourceDevice
                        buttons: [Qt.Key_Alt]
                    }
                ]
            }
        ]
        axes: [
            Axis {
                id: axisMX
                inputs: [
                    AnalogAxisInput {
                        sourceDevice: mouseSourceDevice
                        axis: MouseDevice.X
                    }
                ]
            },
            Axis {
                id: axisMY
                inputs: [
                    AnalogAxisInput {
                        sourceDevice: mouseSourceDevice
                        axis: MouseDevice.Y
                    }
                ]
            }
        ]
    }
}
