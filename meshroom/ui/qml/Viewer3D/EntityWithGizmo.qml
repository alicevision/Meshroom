import Qt3D.Core 2.6
import Qt3D.Render 2.6
import Qt3D.Input 2.6
import Qt3D.Extras 2.15
import Qt3D.Logic 2.6
import QtQuick

/**
 * Wrapper for TransformGizmo.
 * Must be instantiated to control an other entity.
 * The goal is to instantiate the other entity inside this wrapper to gather the object and the gizmo.
 * objectTranform is the component the other entity should use as a Transform.
 */

Entity {
    id: root
    property DefaultCameraController sceneCameraController
    property Layer frontLayerComponent
    property var window
    property alias uniformScale: transformGizmo.uniformScale  // By default, if not set, the value is: false
    property TransformGizmo transformGizmo: TransformGizmo {
        id: transformGizmo
        camera: root.camera
        windowSize: root.windowSize
        frontLayerComponent: root.frontLayerComponent
        window: root.window

        onPickedChanged: function(pressed) {
            sceneCameraController.loseMouseFocus = pressed  // Notify the camera if the transform takes/releases the focus
        }
    }

    readonly property Camera camera : sceneCameraController.camera
    readonly property var windowSize: sceneCameraController.windowSize
    readonly property alias objectTransform : transformGizmo.objectTransform  // The Transform the object should use
}