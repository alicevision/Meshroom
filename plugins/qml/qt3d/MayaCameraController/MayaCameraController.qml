import QtQuick 2.7
import Qt3D.Core 2.0
import Qt3D.Render 2.0
import Qt3D.Input 2.0
import Qt3D.Extras 2.0
import Qt3D.Logic 2.0
import QtQml 2.2

Entity {

    id: root
    property Camera camera
    property real translateSpeed: 100.0
    property real tiltSpeed: -500.0
    property real panSpeed: 500.0

    signal leftClicked(var mouse);
    signal rightClicked(var mouse);

    KeyboardDevice { id: keyboardSourceDevice }
    MouseDevice { id: mouseSourceDevice; sensitivity: 0.1 }

    MouseHandler {
        sourceDevice: mouseSourceDevice
        onReleased: {
            if(mouse.modifiers & Qt.AltModifier)
                return;
            switch(mouse.button) {
                case Qt.LeftButton:
                    leftClicked(mouse)
                    break;
                case Qt.RightButton:
                    rightClicked(mouse)
                    break;
            }
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
                if(!actionAlt.active)
                    return;
                if(actionLMB.active) { // rotate
                    var rx = -axisMX.value;
                    var ry = axisMY.value;
                    root.camera.panAboutViewCenter(root.panSpeed * rx * dt)
                    root.camera.tiltAboutViewCenter(root.tiltSpeed * ry * dt)
                }
                if(actionMMB.active) { // translate
                    var tx = axisMX.value * root.translateSpeed;
                    var ty = axisMY.value * root.translateSpeed;
                    root.camera.translate(Qt.vector3d(-tx, -ty, 0).times(dt))
                }
                if(actionRMB.active) { // zoom
                    var tz = axisMX.value * root.translateSpeed;
                    root.camera.translate(Qt.vector3d(0, 0, tz).times(dt))
                }
            }
        }
    ]
}
