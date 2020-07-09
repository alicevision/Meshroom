import Qt3D.Core 2.0
import Qt3D.Render 2.9
import Qt3D.Input 2.0
import Qt3D.Extras 2.10
import QtQuick 2.9
import Qt3D.Logic 2.0

Entity {
    id: root
    property DefaultCameraController cameraController
    property Layer frontLayerComponent

    readonly property Camera camera : cameraController.camera
    readonly property var windowSize: cameraController.windowSize
    readonly property alias objectTransform : transformGizmo.objectTransform // The Transform the object should use
    
    signal pickedChanged(bool pressed)

    onPickedChanged: {
        cameraController.loseMouseFocus = pressed // Notify the camera if the transform takes/releases the focus
    }

    TransformGizmo {
        id: transformGizmo
        camera: root.camera
        windowSize: root.windowSize
        frontLayerComponent: root.frontLayerComponent
        onPickedChanged: {
            root.pickedChanged(pressed)
        }
    }
}