import QtQuick 2.7
import Qt3D.Core 2.1
import Qt3D.Render 2.1
import Qt3D.Input 2.1
import Qt3D.Logic 2.0
import QtQml 2.2

Entity {
    id: root

    property Camera camera
    property real translateSpeed: 75.0
    property real tiltSpeed: 500.0
    property real panSpeed: 500.0
    property bool moving: pressed || (actionAlt.active && keyboardHandler._pressed)
    property alias focus: keyboardHandler.focus
    readonly property bool pickingActive: actionControl.active && keyboardHandler._pressed
    property real rotationSpeed: 2.0
    property size windowSize
    property real trackballSize: 1.0

    readonly property alias pressed: mouseHandler._pressed
    signal mousePressed(var mouse)
    signal mouseReleased(var mouse)
    signal mouseClicked(var mouse)
    signal mouseWheeled(var wheel)
    signal mouseDoubleClicked(var mouse)

    KeyboardDevice { id: keyboardSourceDevice }
    MouseDevice { id: mouseSourceDevice }

    MouseHandler {
        id: mouseHandler
        property bool _pressed
        property point lastPosition
        property point currentPosition
        sourceDevice: mouseSourceDevice
        onPressed: {
            _pressed = true;
            currentPosition = lastPosition = Qt.point(mouse.x, mouse.y);
            mousePressed(mouse);
        }
        onReleased: {
            _pressed = false;
            mouseReleased(mouse);
        }
        onClicked: mouseClicked(mouse)
        onPositionChanged: { currentPosition = Qt.point(mouse.x, mouse.y) }
        onDoubleClicked: mouseDoubleClicked(mouse)
        onWheel: {
            var d = (root.camera.viewCenter.minus(root.camera.position)).length() * 0.2;
            var tz = (wheel.angleDelta.y / 120) * d;
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
        onFocusChanged: if(!focus) _pressed = false
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

    // Based on the C++ version from https://github.com/cjmdaixi/Qt3DTrackball
    function projectToTrackball(screenCoords)
    {
        var sx = screenCoords.x, sy = windowSize.height - screenCoords.y;
        var p2d = Qt.vector2d(sx / windowSize.width - 0.5, sy / windowSize.height - 0.5);
        var z = 0.0;
        var r2 = trackballSize * trackballSize;
        var lengthSquared = p2d.length() * p2d.length();
        if(lengthSquared <= r2 * 0.5)
            z = Math.sqrt(r2 - lengthSquared);
        else
            z = r2 * 0.5 / p2d.length();
        return Qt.vector3d(p2d.x, p2d.y, z);
    }

    function clamp(x)
    {
        return Math.max(-1, Math.min(x, 1));
    }

    function createRotation(firstPoint, nextPoint)
    {
        var lastPos3D = projectToTrackball(firstPoint).normalized();
        var currentPos3D = projectToTrackball(nextPoint).normalized();
        var obj = {};
        obj.angle = Math.acos(clamp(currentPos3D.dotProduct(lastPos3D)));
        obj.dir = currentPos3D.crossProduct(lastPos3D);
        return obj;
    }

    components: [
        FrameAction {
            onTriggered: {
                if(actionMMB.active || (actionLMB.active && actionShift.active)) { // translate
                    var d = (root.camera.viewCenter.minus(root.camera.position)).length() * 0.03;
                    var tx = axisMX.value * root.translateSpeed * d;
                    var ty = axisMY.value * root.translateSpeed * d;
                    root.camera.translate(Qt.vector3d(-tx, -ty, 0).times(dt))
                    return;
                }
                if(actionLMB.active){ // trackball rotation
                    var res = createRotation(mouseHandler.lastPosition, mouseHandler.currentPosition);
                    var transform = root.camera.components[1]; // transform is camera first component
                    var currentRotation = transform.rotation;
                    var rotatedAxis = Scene3DHelper.rotatedVector(transform.rotation, res.dir);
                    res.angle *= rotationSpeed * dt;
                    root.camera.rotateAboutViewCenter(transform.fromAxisAndAngle(rotatedAxis, res.angle * Math.PI * 180));
                    mouseHandler.lastPosition = mouseHandler.currentPosition;
                    return;
                }
                if(actionAlt.active && actionRMB.active) { // zoom with alt + RMD
                    var d = (root.camera.viewCenter.minus(root.camera.position)).length() * 0.1;
                    var tz = axisMX.value * root.translateSpeed * d;
                    root.camera.translate(Qt.vector3d(0, 0, tz).times(dt), Camera.DontTranslateViewCenter)
                    return;
                }
            }
        }
    ]
}
