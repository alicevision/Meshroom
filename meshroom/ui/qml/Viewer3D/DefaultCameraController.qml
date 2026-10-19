import QtQuick
import Qt3D.Core 2.6
import Qt3D.Render 2.6
import Qt3D.Input 2.6
import Qt3D.Logic 2.6
import QtQml

import Meshroom.Helpers 1.0

Entity {
    id: root

    property Camera camera
    property real tiltSpeed: 500.0
    property real panSpeed: 500.0
    property alias focus: keyboardHandler.focus
    readonly property bool pickingActive: actionControl.active && keyboardHandler._pressed
    property alias rotationSpeed: turntable.rotationSpeed
    property alias zoomToCursor: turntable.zoomToCursor
    property alias windowSize: turntable.windowSize

    property bool loseMouseFocus: false  // Must be changed by other entities when they want to take mouse focus

    property bool moving: false
    property bool panning: false
    property bool zooming: false

    readonly property alias pressed: mouseHandler._pressed
    signal mousePressed(var mouse)
    signal mouseReleased(var mouse, var moved)
    signal mouseClicked(var mouse)
    signal mouseWheeled(var wheel)
    signal mouseDoubleClicked(var mouse)

    KeyboardDevice { id: keyboardSourceDevice }
    MouseDevice { id: mouseSourceDevice }

    TurntableCameraController {
        id: turntable
        camera: root.camera
    }

    MouseHandler {
        id: mouseHandler
        property bool _pressed
        property point pressPosition
        property point lastPosition
        property point currentPosition
        property bool hasMoved
        sourceDevice: loseMouseFocus ? null : mouseSourceDevice
        onPressed: function(mouse) {
            _pressed = true
            pressPosition.x = currentPosition.x = lastPosition.x = mouse.x
            pressPosition.y = currentPosition.y = lastPosition.y = mouse.y
            hasMoved = false
            mousePressed(mouse)
        }
        onReleased: function(mouse) {
            _pressed = false
            mouseReleased(mouse, hasMoved)
        }
        onClicked: function(mouse) {
            mouseClicked(mouse)
        }
        onPositionChanged: function(mouse) {
            currentPosition.x = mouse.x
            currentPosition.y = mouse.y

            root.moving = mouse.buttons & Qt.LeftButton
            root.panning = (mouse.buttons & Qt.MiddleButton)
            var panningAlt = actionShift.active && (mouse.buttons & Qt.LeftButton)
            root.zooming = actionAlt.active && (mouse.buttons & Qt.RightButton)

            if (panning || panningAlt) {  // Translate in the view plane
                turntable.pan(mouseHandler.lastPosition, mouseHandler.currentPosition)
            } else if (moving) {  // Orbit around the view center
                turntable.rotate(mouseHandler.lastPosition, mouseHandler.currentPosition)
            } else if (zooming) {  // Zoom with alt + RMB, towards the point the drag started from
                turntable.zoomByDrag(mouseHandler.pressPosition, mouseHandler.lastPosition, mouseHandler.currentPosition)
            } else {
                return
            }

            mouseHandler.lastPosition = mouseHandler.currentPosition
            mouseHandler.hasMoved = true
        }

        onDoubleClicked: function(mouse) { mouseDoubleClicked(mouse) }
        onWheel: function(wheel) {
            const angleStep = 120  // Angle reported by one mouse wheel notch
            turntable.zoom(wheel.angleDelta.y / angleStep, Qt.point(wheel.x, wheel.y))
        }
    }

    KeyboardHandler {
        id: keyboardHandler
        sourceDevice: keyboardSourceDevice
        property bool _pressed

        // When focus is lost while pressing a key, the corresponding action stays active, even when it is released.
        // Handle this issue manually by keeping an additional _pressed state
        // which is cleared when focus changes (used for 'pickingActive' property).
        onFocusChanged: function(focus) {
            if (!focus)
                _pressed = false
        }
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
    }
}
