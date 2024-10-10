import Qt3D.Core 2.6
import Qt3D.Render 2.6
import Qt3D.Input 2.6
import Qt3D.Extras 2.15

import QtQuick

/**
 * Gizmo for SfMTransform node.
 * Uses EntityWithGizmo wrapper because we should not instantiate TransformGizmo alone.
 */

Entity {
    id: root
    property DefaultCameraController sceneCameraController
    property Layer frontLayerComponent
    property var window
    property var currentSfMTransformNode: null
    enabled: true
    
    readonly property alias objectTransform: sfmTranformGizmoEntity.objectTransform // The Transform the object should use

    EntityWithGizmo {
        id: sfmTranformGizmoEntity
        sceneCameraController: root.sceneCameraController
        frontLayerComponent: root.frontLayerComponent
        window: root.window
        uniformScale: true  // We want to make uniform scale transformations

        // Update node SfMTransform slider values when the gizmo has changed: translation, rotation, scale, type
        transformGizmo.onGizmoChanged: {
            switch (type) {
                case TransformGizmo.Type.TRANSLATION: {
                    _reconstruction.setAttribute(
                        root.currentSfMTransformNode.attribute("manualTransform.manualTranslation"),
                        JSON.stringify([translation.x, translation.y, translation.z])
                    )
                    break
                }
                case TransformGizmo.Type.ROTATION: {
                    _reconstruction.setAttribute(
                        root.currentSfMTransformNode.attribute("manualTransform.manualRotation"),
                        JSON.stringify([rotation.x, rotation.y, rotation.z])
                    )
                    break
                }
                case TransformGizmo.Type.SCALE: {
                    // Only one scale is needed since the scale is uniform
                    _reconstruction.setAttribute(
                        root.currentSfMTransformNode.attribute("manualTransform.manualScale"),
                        scale.x
                    )
                    break
                }
                case TransformGizmo.Type.ALL: {
                    _reconstruction.setAttribute(
                        root.currentSfMTransformNode.attribute("manualTransform"),
                        JSON.stringify([
                            [translation.x, translation.y, translation.z],
                            [rotation.x, rotation.y, rotation.z],
                            scale.x
                        ])
                    )
                    break
                }
            }
        }

        // Translation values from node (vector3d because this is the type of QTransform.translation)
        property var nodeTranslation : Qt.vector3d(
            root.currentSfMTransformNode ? root.currentSfMTransformNode.attribute("manualTransform.manualTranslation.x").value : 0,
            root.currentSfMTransformNode ? root.currentSfMTransformNode.attribute("manualTransform.manualTranslation.y").value : 0,
            root.currentSfMTransformNode ? root.currentSfMTransformNode.attribute("manualTransform.manualTranslation.z").value : 0
        )
        // Rotation values from node (3 separated values because QTransform stores Euler angles like this)
        property var nodeRotationX: root.currentSfMTransformNode ? root.currentSfMTransformNode.attribute("manualTransform.manualRotation.x").value : 0
        property var nodeRotationY: root.currentSfMTransformNode ? root.currentSfMTransformNode.attribute("manualTransform.manualRotation.y").value : 0
        property var nodeRotationZ: root.currentSfMTransformNode ? root.currentSfMTransformNode.attribute("manualTransform.manualRotation.z").value : 0
        // Scale value from node (simple number because we use uniform scale)
        property var nodeScale: root.currentSfMTransformNode ? root.currentSfMTransformNode.attribute("manualTransform.manualScale").value : 1

        // Automatically evaluate the Transform: value is taken from the node OR from the actual modification if the gizmo is moved by mouse.
        // When the gizmo has changed (with mouse), the new values are set to the node, the priority is given back to the node and the Transform is re-evaluated once with those values.
        transformGizmo.gizmoDisplayTransform.translation: transformGizmo.focusGizmoPriority ? transformGizmo.gizmoDisplayTransform.translation : nodeTranslation
        transformGizmo.gizmoDisplayTransform.rotationX: transformGizmo.focusGizmoPriority ? transformGizmo.gizmoDisplayTransform.rotationX : nodeRotationX
        transformGizmo.gizmoDisplayTransform.rotationY: transformGizmo.focusGizmoPriority ? transformGizmo.gizmoDisplayTransform.rotationY : nodeRotationY
        transformGizmo.gizmoDisplayTransform.rotationZ: transformGizmo.focusGizmoPriority ? transformGizmo.gizmoDisplayTransform.rotationZ : nodeRotationZ
        transformGizmo.objectTransform.scale3D: transformGizmo.focusGizmoPriority ? transformGizmo.objectTransform.scale3D : Qt.vector3d(nodeScale, nodeScale, nodeScale)
    }
}
