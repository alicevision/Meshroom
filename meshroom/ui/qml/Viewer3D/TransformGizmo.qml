import Qt3D.Core 2.0
import Qt3D.Render 2.9
import Qt3D.Input 2.0
import Qt3D.Extras 2.10
import QtQuick 2.9
import Qt3D.Logic 2.0

Entity {
    id: root
    property real gizmoScale: 0.20
    property Camera camera
    readonly property Transform objectTransform : Transform {}
    
    signal pickedChanged(bool pressed)

    components: [gizmoDisplayTransform, mouseHandler]


    /***** ENUMS *****/

    enum Axis {
        X,
        Y,
        Z
    }

    enum Type {
        POSITION,
        ROTATION,
        SCALE
    }

    /***** QUATERNIONS *****/

    function multiplyQuaternion(q1, q2) {
        return Qt.quaternion(
            q1.scalar * q2.scalar - q1.x * q2.x - q1.y * q2.y - q1.z * q2.z,
            q1.scalar * q2.x + q1.x * q2.scalar + q1.y * q2.z - q1.z * q2.y,
            q1.scalar * q2.y + q1.y * q2.scalar + q1.z * q2.x - q1.x * q2.z,
            q1.scalar * q2.z + q1.z * q2.scalar + q1.x * q2.y - q1.y * q2.x
        )
    }

    function dotQuaternion(q) {
        return (((q.x * q.x) + (q.y * q.y)) + (q.z * q.z)) + (q.scalar * q.scalar)
    }

    function normalizeQuaternion(q) {
        const dot = dotQuaternion(q)
        const inv = 1.0 / (Math.sqrt(dot))
        return Qt.quaternion(q.scalar * inv, q.x * inv, q.y * inv, q.z * inv)
    }

    function quaternionFromAxisAngle(vec3, degree) {
        const rad = degree * Math.PI/180
        const factor = Math.sin(rad/2) // Used for the quaternion computation

        // Compute the quaternion
        const x = vec3.x * factor
        const y = vec3.y * factor
        const z = vec3.z * factor
        const w = Math.cos(rad/2)

        return normalizeQuaternion(Qt.quaternion(w, x, y, z))
    }

    function quaternionToRotationMatrix(q) {
        const w = q.scalar
        const x = q.x
        const y = q.y
        const z = q.z

        return Qt.matrix4x4(
            w*w + x*x - y*y - z*z, 2*(x*y - w*z), 2*(w*y + x*z), 0,
            2*(x*y + w*z), w*w - x*x + y*y - z*z, 2*(y*z - w*x), 0,
            2*(x*z - w*y), 2*(w*x + y*z), w*w - x*x - y*y + z*z, 0,
            0,             0,             0,                     1
        )
    }
    
    /***** GENERIC MATRIX TRANSFORMATIONS *****/

    function decomposeModelMatrixFromTransform(transform) {
        const posMat = Qt.matrix4x4()
        posMat.translate(transform.translation)
        const rotMat = quaternionToRotationMatrix(transform.rotation)
        const scaleMat = Qt.matrix4x4()
        scaleMat.scale(transform.scale3D)

        return { position: posMat, rotation: rotMat, scale: scaleMat }
    }

    function localTranslate(transform, translateVec) {
        const modelMat = decomposeModelMatrixFromTransform(transform)

        // Compute the translation transformation matrix 
        const translationMat = Qt.matrix4x4()
        translationMat.translate(translateVec)

        // Compute the new model matrix (POSITION * ROTATION * TRANSLATE * SCALE) and set it to the Transform
        const mat = modelMat.position.times(modelMat.rotation.times(translationMat.times(modelMat.scale)))
        transform.setMatrix(mat)       
    }

    function localRotate(transform, axis, degree) {
        const modelMat = decomposeModelMatrixFromTransform(transform) 
        
        // Compute the transformation quaternion from axis and angle in degrees
        let vec3
        switch(axis) {
            case TransformGizmo.Axis.X: vec3 = Qt.vector3d(1,0,0); break
            case TransformGizmo.Axis.Y: vec3 = Qt.vector3d(0,1,0); break
            case TransformGizmo.Axis.Z: vec3 = Qt.vector3d(0,0,1); break
        }
        const transformQuat = quaternionFromAxisAngle(vec3, degree)

        // Get rotation quaternion of the current model matrix
        const initRotQuat = transform.rotation
        // Compute the new rotation quaternion and then calculate the matrix
        const newRotQuat = multiplyQuaternion(initRotQuat, transformQuat) // Order is important
        const newRotationMat = quaternionToRotationMatrix(newRotQuat)

        // Compute the new model matrix (POSITION * NEW_COMPUTED_ROTATION * SCALE) and set it to the Transform
        const mat = modelMat.position.times(newRotationMat.times(modelMat.scale))
        transform.setMatrix(mat)
    }

    function localScale(transform, scaleVec) {
        const modelMat = decomposeModelMatrixFromTransform(transform)

        // Update the scale matrix
        modelMat.scale.m11 += scaleVec.x
        modelMat.scale.m22 += scaleVec.y
        modelMat.scale.m33 += scaleVec.z

        // Compute the new model matrix (POSITION * ROTATION * SCALE) and set it to the Transform
        const mat = modelMat.position.times(modelMat.rotation.times(modelMat.scale))
        transform.setMatrix(mat)
    }

    /***** SPECIFIC MATRIX TRANSFORMATIONS (using local vars) *****/

    function doTranslation(translateVec) {
        localTranslate(gizmoDisplayTransform, translateVec) // Update gizmo matrix
        localTranslate(objectTransform, translateVec) // Update object matrix
    }

    function doRotation(axis, degree) {
        localRotate(gizmoDisplayTransform, axis, degree) // Update gizmo matrix
        localRotate(objectTransform, axis, degree) // Update object matrix
    }

    function doScale(scaleVec) {
        localScale(objectTransform, scaleVec) // Update object matrix
    }

    /***** DEVICES *****/

    MouseDevice { id: mouseSourceDevice }

    MouseHandler {
        id: mouseHandler
        sourceDevice: mouseSourceDevice
        property point lastPosition
        property point currentPosition
        onPositionChanged: {
            currentPosition.x = mouse.x
            currentPosition.y = mouse.y
        }
    }

    /***** GIZMO'S BASIC COMPONENTS *****/

    Transform {
        id: gizmoDisplayTransform
        scale: {
            return root.gizmoScale * (camera.position.minus(gizmoDisplayTransform.translation)).length()
        }
    }

    Entity {
        id: centerSphereEntity
        components: [centerSphereMesh, centerSphereMaterial]

        SphereMesh {
            id: centerSphereMesh
            radius: 0.04
            rings: 8
            slices: 8
        }
        PhongMaterial {
            id: centerSphereMaterial
            property color base: "white"
            ambient: base
            shininess: 0.2
        }
    }

    // AXIS GIZMO INSTANTIATOR => X, Y and Z
    NodeInstantiator {
        model: 3

        Entity {
            id: axisContainer
            property int axis : {
                switch(index) {
                    case 0: return TransformGizmo.Axis.X
                    case 1: return TransformGizmo.Axis.Y
                    case 2: return TransformGizmo.Axis.Z
                }                
            }
            property color baseColor: {
                switch(axis) {
                    case TransformGizmo.Axis.X: return "#e63b55"
                    case TransformGizmo.Axis.Y: return "#83c414"
                    case TransformGizmo.Axis.Z: return "#3387e2"
                }
            }
            property real lineRadius: 0.015

            // SCALE ENTITY
            Entity {
                id: scaleEntity

                Entity {
                    id: axisCylinder
                    components: [cylinderMesh, cylinderTransform, scaleMaterial]

                    CylinderMesh {
                        id: cylinderMesh
                        length: 0.5
                        radius: axisContainer.lineRadius
                        rings: 2
                        slices: 16
                    }
                    Transform {
                        id: cylinderTransform
                        matrix: {
                            const offset = cylinderMesh.length/2 + centerSphereMesh.radius
                            const m = Qt.matrix4x4()
                            switch(axis) {
                                case TransformGizmo.Axis.X: {
                                    m.translate(Qt.vector3d(offset, 0, 0))
                                    m.rotate(90, Qt.vector3d(0,0,1)) 
                                    break
                                }   
                                case TransformGizmo.Axis.Y: {
                                    m.translate(Qt.vector3d(0, offset, 0))
                                    break
                                }
                                case TransformGizmo.Axis.Z: {
                                    m.translate(Qt.vector3d(0, 0, offset))
                                    m.rotate(90, Qt.vector3d(1,0,0))
                                    break
                                }
                            }
                            return m
                        }
                    }
                }

                Entity {
                    id: axisScaleBox
                    components: [cubeScaleMesh, cubeScaleTransform, scaleMaterial, scalePicker]

                    CuboidMesh {
                        id: cubeScaleMesh
                        property real edge: 0.07
                        xExtent: edge
                        yExtent: edge
                        zExtent: edge
                    }
                    Transform {
                        id: cubeScaleTransform
                        matrix: {
                            const offset = cylinderMesh.length + centerSphereMesh.radius
                            const m = Qt.matrix4x4()
                            switch(axis) {
                                case TransformGizmo.Axis.X: {
                                    m.translate(Qt.vector3d(offset, 0, 0))
                                    m.rotate(90, Qt.vector3d(0,0,1))
                                    break
                                }
                                case TransformGizmo.Axis.Y: {
                                    m.translate(Qt.vector3d(0, offset, 0))
                                    break
                                }
                                case TransformGizmo.Axis.Z: {
                                    m.translate(Qt.vector3d(0, 0, offset))
                                    m.rotate(90, Qt.vector3d(1,0,0))
                                    break
                                }
                            }
                            return m
                        }
                    }
                }

                PhongMaterial {
                    id: scaleMaterial
                    ambient: baseColor
                }

                TransformGizmoPicker { 
                    id: scalePicker
                    mouseController: mouseHandler
                    gizmoMaterial: scaleMaterial
                    gizmoBaseColor: baseColor
                    gizmoAxis: axis
                    gizmoType: TransformGizmo.Type.SCALE

                    onPickedChanged: {
                        root.pickedChanged(picker.isPressed) // Used to prevent camera transformations
                        transformHandler.objectPicker = picker.isPressed ? picker : null // Pass the picker to the global FrameAction
                    }
                }
            }

            // POSITION ENTITY
            Entity {
                id: positionEntity
                components: [coneMesh, coneTransform, positionMaterial, positionPicker]

                ConeMesh {
                    id: coneMesh
                    bottomRadius : 0.04
                    topRadius : 0.001
                    hasBottomEndcap : true
                    hasTopEndcap : true
                    length : 0.15
                    rings : 2
                    slices : 8
                }
                Transform {
                    id: coneTransform
                    matrix: {
                        const offset = cylinderMesh.length + centerSphereMesh.radius + 0.4
                        const m = Qt.matrix4x4()
                        switch(axis) {
                            case TransformGizmo.Axis.X: {
                                m.translate(Qt.vector3d(offset, 0, 0))
                                m.rotate(-90, Qt.vector3d(0,0,1))
                                break
                            }
                            case TransformGizmo.Axis.Y: {
                                m.translate(Qt.vector3d(0, offset, 0))
                                break
                            }
                            case TransformGizmo.Axis.Z: {
                                m.translate(Qt.vector3d(0, 0, offset))
                                m.rotate(90, Qt.vector3d(1,0,0))
                                break
                            }
                        }
                        return m
                    }
                }
                PhongMaterial {
                    id: positionMaterial
                    ambient: baseColor
                }

                TransformGizmoPicker { 
                    id: positionPicker
                    mouseController: mouseHandler
                    gizmoMaterial: positionMaterial
                    gizmoBaseColor: baseColor
                    gizmoAxis: axis
                    gizmoType: TransformGizmo.Type.POSITION

                    onPickedChanged: {
                        root.pickedChanged(picker.isPressed) // Used to prevent camera transformations
                        transformHandler.objectPicker = picker.isPressed ? picker : null // Pass the picker to the global FrameAction
                    }
                }
            }

            // ROTATION ENTITY
            Entity {
                id: rotationEntity
                components: [torusMesh, torusTransform, rotationMaterial, rotationPicker]

                TorusMesh {
                    id: torusMesh
                    radius: cylinderMesh.length + 0.25
                    minorRadius: axisContainer.lineRadius
                    slices: 8
                    rings: 32
                }
                Transform {
                    id: torusTransform
                    matrix: {
                        const scaleDiff = 2*torusMesh.minorRadius + 0.01 // Just to make sure there is no face overlapping
                        const m = Qt.matrix4x4()
                        switch(axis) {
                            case TransformGizmo.Axis.X: m.rotate(90, Qt.vector3d(0,1,0)); break
                            case TransformGizmo.Axis.Y: m.rotate(90, Qt.vector3d(1,0,0)); m.scale(Qt.vector3d(1-scaleDiff, 1-scaleDiff, 1-scaleDiff)); break
                            case TransformGizmo.Axis.Z: m.scale(Qt.vector3d(1-2*scaleDiff, 1-2*scaleDiff, 1-2*scaleDiff)); break
                        }
                        return m
                    }
                }
                PhongMaterial {
                    id: rotationMaterial
                    ambient: baseColor
                }

                TransformGizmoPicker { 
                    id: rotationPicker
                    mouseController: mouseHandler
                    gizmoMaterial: rotationMaterial
                    gizmoBaseColor: baseColor
                    gizmoAxis: axis
                    gizmoType: TransformGizmo.Type.ROTATION

                    onPickedChanged: {
                        root.pickedChanged(picker.isPressed) // Used to prevent camera transformations
                        transformHandler.objectPicker = picker.isPressed ? picker : null // Pass the picker to the global FrameAction
                    }
                }
            }
        }
    }

    FrameAction {
        id: transformHandler
        property var objectPicker: null

        onTriggered: {
            if (objectPicker) {
                switch(objectPicker.gizmoType) {
                    case TransformGizmo.Type.POSITION: {
                        const offsetX = mouseHandler.currentPosition.x - mouseHandler.lastPosition.x
                        const offsetY = mouseHandler.currentPosition.y - mouseHandler.lastPosition.y

                        let pickedAxis
                        switch(objectPicker.gizmoAxis) {
                            case TransformGizmo.Axis.X: pickedAxis = Qt.vector3d(1,0,0); break
                            case TransformGizmo.Axis.Y: pickedAxis = Qt.vector3d(0,1,0); break
                            case TransformGizmo.Axis.Z: pickedAxis = Qt.vector3d(0,0,1); break
                        }

                        doTranslation(pickedAxis.times(0.01*offsetX - 0.01*offsetY))
                        mouseHandler.lastPosition = mouseHandler.currentPosition
                        return
                    }

                    case TransformGizmo.Type.ROTATION: {
                        const offsetX = mouseHandler.currentPosition.x - mouseHandler.lastPosition.x
                        const offsetY = mouseHandler.currentPosition.y - mouseHandler.lastPosition.y
                        // const offset = 0.1*offsetX - 0.1*offsetY
                        const offset = 1

                        doRotation(objectPicker.gizmoAxis, offset)
                        mouseHandler.lastPosition = mouseHandler.currentPosition
                        return
                    }

                    case TransformGizmo.Type.SCALE: {
                        const offsetX = mouseHandler.currentPosition.x - mouseHandler.lastPosition.x
                        const offsetY = mouseHandler.currentPosition.y - mouseHandler.lastPosition.y
                        // const offset = 0.1*offsetX - 0.1*offsetY
                        const offset = 0.05

                        let pickedAxis
                        switch(objectPicker.gizmoAxis) {
                            case TransformGizmo.Axis.X: pickedAxis = Qt.vector3d(1,0,0); break
                            case TransformGizmo.Axis.Y: pickedAxis = Qt.vector3d(0,1,0); break
                            case TransformGizmo.Axis.Z: pickedAxis = Qt.vector3d(0,0,1); break
                        }

                        doScale(pickedAxis.times(offset))
                        mouseHandler.lastPosition = mouseHandler.currentPosition
                        return      
                    }
                }
            }
        }
    }
}
