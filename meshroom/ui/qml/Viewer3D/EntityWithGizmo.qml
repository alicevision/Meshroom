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
    property var window

    readonly property Camera camera : cameraController.camera
    readonly property var windowSize: cameraController.windowSize
    readonly property alias objectTransform : transformGizmo.objectTransform // The Transform the object should use
    readonly property alias updateTransformations: transformGizmo.updateTransformations // Function to update the transformations
    
    signal pickedChanged(bool pressed)
    signal gizmoChanged(var translation, var rotation, var scale)

    onPickedChanged: {
        cameraController.loseMouseFocus = pressed // Notify the camera if the transform takes/releases the focus
    }

    TransformGizmo {
        id: transformGizmo
        camera: root.camera
        windowSize: root.windowSize
        frontLayerComponent: root.frontLayerComponent
        window: root.window
        onPickedChanged: {
            root.pickedChanged(pressed)
        }
        onGizmoChanged: {
            root.gizmoChanged(translation, rotation, scale)
        }
    }
}