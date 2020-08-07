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
    property var currentMeshingNode: null
    enabled: true

    EntityWithGizmo {
        id: boundingBoxEntity
        sceneCameraController: root.sceneCameraController
        frontLayerComponent: root.frontLayerComponent
        window: root.window

        // Update node meshing slider values when the gizmo has changed: translation, rotation, scale, type
        transformGizmo.onGizmoChanged: {
            switch(type) {
                case TransformGizmo.Type.TRANSLATION: {
                    _reconstruction.setAttribute(
                        root.currentMeshingNode.attribute("boundingBox.bboxTranslation"),
                        JSON.stringify([translation.x, translation.y, translation.z])
                    )
                    break
                }
                case TransformGizmo.Type.ROTATION: {
                    _reconstruction.setAttribute(
                        root.currentMeshingNode.attribute("boundingBox.bboxRotation"),
                        JSON.stringify([rotation.x, rotation.y, rotation.z])
                    )
                    break
                }
                case TransformGizmo.Type.SCALE: {
                    _reconstruction.setAttribute(
                        root.currentMeshingNode.attribute("boundingBox.bboxScale"),
                        JSON.stringify([scale.x, scale.y, scale.z])
                    )
                    break
                }
                case TransformGizmo.Type.ALL: {
                    _reconstruction.setAttribute(
                        root.currentMeshingNode.attribute("boundingBox"),
                        JSON.stringify([
                            [translation.x, translation.y, translation.z],
                            [rotation.x, rotation.y, rotation.z],
                            [scale.x, scale.y, scale.z]
                        ])
                    )
                    break
                }
            }
        }

        // Automatically evaluate the Transform: value is taken from the node OR from the actual modification if the gizmo is moved by mouse.
        // When the gizmo has changed (with mouse), the new values are set to the node, the priority is given back to the node and the Transform is re-evaluated once with those values.
        property var nodeTranslation : Qt.vector3d(
            root.currentMeshingNode.attribute("boundingBox.bboxTranslation.x").value,
            root.currentMeshingNode.attribute("boundingBox.bboxTranslation.y").value,
            root.currentMeshingNode.attribute("boundingBox.bboxTranslation.z").value
        )
        property var nodeRotationX: root.currentMeshingNode.attribute("boundingBox.bboxRotation.x").value
        property var nodeRotationY: root.currentMeshingNode.attribute("boundingBox.bboxRotation.y").value
        property var nodeRotationZ: root.currentMeshingNode.attribute("boundingBox.bboxRotation.z").value
        property var nodeScale: Qt.vector3d(
            root.currentMeshingNode.attribute("boundingBox.bboxScale.x").value,
            root.currentMeshingNode.attribute("boundingBox.bboxScale.y").value,
            root.currentMeshingNode.attribute("boundingBox.bboxScale.z").value
        )

        transformGizmo.gizmoDisplayTransform.translation: transformGizmo.focusGizmoPriority ? transformGizmo.gizmoDisplayTransform.translation : nodeTranslation
        transformGizmo.gizmoDisplayTransform.rotationX: transformGizmo.focusGizmoPriority ? transformGizmo.gizmoDisplayTransform.rotationX : nodeRotationX
        transformGizmo.gizmoDisplayTransform.rotationY: transformGizmo.focusGizmoPriority ? transformGizmo.gizmoDisplayTransform.rotationY : nodeRotationY
        transformGizmo.gizmoDisplayTransform.rotationZ: transformGizmo.focusGizmoPriority ? transformGizmo.gizmoDisplayTransform.rotationZ : nodeRotationZ
        transformGizmo.objectTransform.scale3D: transformGizmo.focusGizmoPriority ? transformGizmo.objectTransform.scale3D : nodeScale

        // The entity
        BoundingBox { transform: boundingBoxEntity.objectTransform }
    }
}
