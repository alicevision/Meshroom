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
    property bool moving: pressed || actionAlt.active
    readonly property alias controlPressed: actionControl.active

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
        sourceDevice: mouseSourceDevice
        onPressed: { _pressed = true; mousePressed(mouse) }
        onReleased: { _pressed = false; mouseReleased(mouse)  }
        onClicked: mouseClicked(mouse)
        onDoubleClicked: mouseDoubleClicked(mouse)
        onWheel: {
            var d = (root.camera.viewCenter.minus(root.camera.position)).length() * 0.2;
            var tz = (wheel.angleDelta.y / 120) * d;
            root.camera.translate(Qt.vector3d(0, 0, tz), Camera.DontTranslateViewCenter)
        }
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

    components: [
        FrameAction {
            onTriggered: {
                if(actionMMB.active || (actionLMB.active && actionControl.active)) { // translate
                    var d = (root.camera.viewCenter.minus(root.camera.position)).length() * 0.03;
                    var tx = axisMX.value * root.translateSpeed * d;
                    var ty = axisMY.value * root.translateSpeed * d;
                    root.camera.translate(Qt.vector3d(-tx, -ty, 0).times(dt))
                    return;
                }
                if(actionLMB.active) { // rotate
                    var rx = -axisMX.value;
                    var ry = -axisMY.value;
                    root.camera.panAboutViewCenter(root.panSpeed * rx * dt, Qt.vector3d(0,1,0))
                    root.camera.tiltAboutViewCenter(root.tiltSpeed * ry * dt)
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
