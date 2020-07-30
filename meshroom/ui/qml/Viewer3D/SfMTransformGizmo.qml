import Qt3D.Core 2.0
import Qt3D.Render 2.9
import Qt3D.Input 2.0
import Qt3D.Extras 2.10
import QtQuick 2.9

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
        uniformScale: true // We want to make uniform scale transformations

        // Update node SfMTransform slider values when the gizmo has changed: translation, rotation, scale
        transformGizmo.onGizmoChanged: {
            _reconstruction.setAttribute(root.currentSfMTransformNode.attribute("manualTransform.manualTranslation.x"), translation.x)
            _reconstruction.setAttribute(root.currentSfMTransformNode.attribute("manualTransform.manualTranslation.y"), translation.y)
            _reconstruction.setAttribute(root.currentSfMTransformNode.attribute("manualTransform.manualTranslation.z"), translation.z)

            _reconstruction.setAttribute(root.currentSfMTransformNode.attribute("manualTransform.manualRotation.x"), rotation.x)
            _reconstruction.setAttribute(root.currentSfMTransformNode.attribute("manualTransform.manualRotation.y"), rotation.y)
            _reconstruction.setAttribute(root.currentSfMTransformNode.attribute("manualTransform.manualRotation.z"), rotation.z)

            // Only one scale is needed since the scale is uniform
            _reconstruction.setAttribute(root.currentSfMTransformNode.attribute("manualTransform.manualScale"), scale.x)
        }

        // Automatically evalutate the Transform: value is taken from the node OR from the actual modification if the gizmo is moved by mouse.
        // When the gizmo has changed (with mouse), the new values are set to the node, the priority is given back to the node and the Transform is re-evaluated once with those values.
        property var nodeTranslation : Qt.vector3d(
            root.currentSfMTransformNode.attribute("manualTransform.manualTranslation.x").value,
            root.currentSfMTransformNode.attribute("manualTransform.manualTranslation.y").value,
            root.currentSfMTransformNode.attribute("manualTransform.manualTranslation.z").value
        )
        property var nodeRotationX: root.currentSfMTransformNode.attribute("manualTransform.manualRotation.x").value
        property var nodeRotationY: root.currentSfMTransformNode.attribute("manualTransform.manualRotation.y").value
        property var nodeRotationZ: root.currentSfMTransformNode.attribute("manualTransform.manualRotation.z").value
        property var nodeScale: root.currentSfMTransformNode.attribute("manualTransform.manualScale").value

        transformGizmo.gizmoDisplayTransform.translation: transformGizmo.focusGizmoPriority ? transformGizmo.gizmoDisplayTransform.translation : nodeTranslation
        transformGizmo.gizmoDisplayTransform.rotationX: transformGizmo.focusGizmoPriority ? transformGizmo.gizmoDisplayTransform.rotationX : nodeRotationX
        transformGizmo.gizmoDisplayTransform.rotationY: transformGizmo.focusGizmoPriority ? transformGizmo.gizmoDisplayTransform.rotationY : nodeRotationY
        transformGizmo.gizmoDisplayTransform.rotationZ: transformGizmo.focusGizmoPriority ? transformGizmo.gizmoDisplayTransform.rotationZ : nodeRotationZ
        transformGizmo.objectTransform.scale3D: transformGizmo.focusGizmoPriority ? transformGizmo.objectTransform.scale3D : Qt.vector3d(nodeScale, nodeScale, nodeScale)
    }
}
