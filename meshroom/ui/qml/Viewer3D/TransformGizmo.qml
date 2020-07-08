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
    property var windowSize
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

    function pointFromWorldToScreen(point, camera, windowSize) {
        // Transform the point from World Coord to Normalized Device Coord
        const viewMatrix = camera.transform.matrix.inverted()
        const projectedPoint = camera.projectionMatrix.times(viewMatrix.times(point))
        const projectedPoint2D = Qt.vector2d(projectedPoint.x/projectedPoint.w, projectedPoint.y/projectedPoint.w)

        // Transform the point from Normalized Device Coord to Screen Coord
        const screenPoint2D = Qt.vector2d(
            parseInt((projectedPoint2D.x + 1) * windowSize.width / 2),
            parseInt((projectedPoint2D.y - 1) * windowSize.height / -2)
        )

        return screenPoint2D
    }

    function decomposeModelMatrixFromTransformations(translation, rotation, scale3D) {
        const posMat = Qt.matrix4x4()
        posMat.translate(translation)
        const rotMat = quaternionToRotationMatrix(rotation)
        const scaleMat = Qt.matrix4x4()
        scaleMat.scale(scale3D)

        const rotQuat = Qt.quaternion(rotation.scalar, rotation.x, rotation.y, rotation.z)

        return { positionMat: posMat, rotationMat: rotMat, scaleMat: scaleMat, quaternion: rotQuat }
    }

    function decomposeModelMatrixFromTransform(transformQtInstance) {
        return decomposeModelMatrixFromTransformations(transformQtInstance.translation, transformQtInstance.rotation, transformQtInstance.scale3D)
    }

    function localTranslate(transformQtInstance, initialDecomposedModelMat, translateVec) {
        // Compute the translation transformation matrix 
        const translationMat = Qt.matrix4x4()
        translationMat.translate(translateVec)

        // Compute the new model matrix (POSITION * ROTATION * TRANSLATE * SCALE) and set it to the Transform
        const mat = initialDecomposedModelMat.positionMat.times(initialDecomposedModelMat.rotationMat.times(translationMat.times(initialDecomposedModelMat.scaleMat)))
        transformQtInstance.setMatrix(mat)
    }

    function localRotate(transformQtInstance, initialDecomposedModelMat, axis, degree) {       
        // Compute the transformation quaternion from axis and angle in degrees
        const transformQuat = quaternionFromAxisAngle(axis, degree)

        // Get rotation quaternion of the current model matrix
        const initRotQuat = initialDecomposedModelMat.quaternion
        // Compute the new rotation quaternion and then calculate the matrix
        const newRotQuat = multiplyQuaternion(initRotQuat, transformQuat) // Order is important
        const newRotationMat = quaternionToRotationMatrix(newRotQuat)

        // Compute the new model matrix (POSITION * NEW_COMPUTED_ROTATION * SCALE) and set it to the Transform
        const mat = initialDecomposedModelMat.positionMat.times(newRotationMat.times(initialDecomposedModelMat.scaleMat))
        transformQtInstance.setMatrix(mat)
    }

    function localScale(transformQtInstance, initialDecomposedModelMat, scaleVec) {
        // Make a copy of the scale matrix (otherwise, it is a reference and it does not work as expected)
        // Unfortunately, we have to proceed like this because, in QML, Qt.matrix4x4(Qt.matrix4x4) does not work
        const scaleMat = Qt.matrix4x4()
        scaleMat.scale(Qt.vector3d(initialDecomposedModelMat.scaleMat.m11, initialDecomposedModelMat.scaleMat.m22, initialDecomposedModelMat.scaleMat.m33))

        // Update the scale matrix copy
        scaleMat.m11 += scaleVec.x
        scaleMat.m22 += scaleVec.y
        scaleMat.m33 += scaleVec.z

        // Compute the new model matrix (POSITION * ROTATION * SCALE) and set it to the Transform
        const mat = initialDecomposedModelMat.positionMat.times(initialDecomposedModelMat.rotationMat.times(scaleMat))
        transformQtInstance.setMatrix(mat)
    }

    /***** SPECIFIC MATRIX TRANSFORMATIONS (using local vars) *****/

    function doTranslation(initialDecomposedModelMat, translateVec) {
        localTranslate(gizmoDisplayTransform, initialDecomposedModelMat, translateVec) // Update gizmo matrix
        localTranslate(objectTransform, initialDecomposedModelMat, translateVec) // Update object matrix
    }

    function doRotation(initialDecomposedModelMat, axis, degree) {
        localRotate(gizmoDisplayTransform, initialDecomposedModelMat, axis, degree) // Update gizmo matrix
        localRotate(objectTransform, initialDecomposedModelMat, axis, degree) // Update object matrix
    }

    function doScale(initialDecomposedModelMat, scaleVec) {
        localScale(objectTransform, initialDecomposedModelMat, scaleVec) // Update object matrix
    }

    /***** DEVICES *****/

    MouseDevice { id: mouseSourceDevice }

    MouseHandler {
        id: mouseHandler
        sourceDevice: mouseSourceDevice
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
                    case TransformGizmo.Axis.X: return "#e63b55" // Red
                    case TransformGizmo.Axis.Y: return "#83c414" // Green
                    case TransformGizmo.Axis.Z: return "#3387e2" // Blue
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
                        this.decomposedObjectModelMat = decomposeModelMatrixFromTransformations(objectTransform.translation, objectTransform.rotation, objectTransform.scale3D) // Save the current transformations
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
                        this.decomposedObjectModelMat = decomposeModelMatrixFromTransformations(objectTransform.translation, objectTransform.rotation, objectTransform.scale3D) // Save the current transformations
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
                        this.decomposedObjectModelMat = decomposeModelMatrixFromTransformations(objectTransform.translation, objectTransform.rotation, objectTransform.scale3D) // Save the current transformations
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

                let pickedAxis
                switch(objectPicker.gizmoAxis) {
                    case TransformGizmo.Axis.X: pickedAxis = Qt.vector3d(1,0,0); break
                    case TransformGizmo.Axis.Y: pickedAxis = Qt.vector3d(0,1,0); break
                    case TransformGizmo.Axis.Z: pickedAxis = Qt.vector3d(0,0,1); break
                }

                switch(objectPicker.gizmoType) {
                    case TransformGizmo.Type.POSITION: {
                        const sensibility = 0.02

                        // Compute the current vector PickedPoint -> CurrentMousePoint
                        const pickedPosition = objectPicker.screenPoint
                        const mouseVector = Qt.vector2d(mouseHandler.currentPosition.x - pickedPosition.x, -(mouseHandler.currentPosition.y - pickedPosition.y))

                        // Transform the positive picked axis vector from World Coord to Screen Coord
                        const gizmoLocalPointOnAxis = gizmoDisplayTransform.matrix.times(Qt.vector4d(pickedAxis.x, pickedAxis.y, pickedAxis.z, 1))
                        const gizmoCenterPoint = gizmoDisplayTransform.matrix.times(Qt.vector4d(0, 0, 0, 1))
                        const screenPoint2D = pointFromWorldToScreen(gizmoLocalPointOnAxis, camera, windowSize)
                        const screenCenter2D = pointFromWorldToScreen(gizmoCenterPoint, camera, windowSize)
                        const screenAxisVector = Qt.vector2d(screenPoint2D.x - screenCenter2D.x, -(screenPoint2D.y - screenCenter2D.y))

                        // Get the cosinus of the angle from the screenAxisVector to the mouseVector
                        const cosAngle = screenAxisVector.dotProduct(mouseVector) / (screenAxisVector.length() * mouseVector.length())
                        const offset = cosAngle * mouseVector.length() * sensibility

                        // If the mouse is not at the same spot as the pickedPoint, we do translation
                        if (offset) doTranslation(objectPicker.decomposedObjectModelMat, pickedAxis.times(offset)) // Do a translation from the initial Object Model Matrix when we picked the gizmo

                        return
                    }

                    case TransformGizmo.Type.ROTATION: {
                        // Get Screen Coordinates of the gizmo center
                        const gizmoCenterPoint = gizmoDisplayTransform.matrix.times(Qt.vector4d(0, 0, 0, 1))
                        const screenCenter2D = pointFromWorldToScreen(gizmoCenterPoint, camera, root.windowSize)

                        // Get the vector screenCenter2D -> PickedPoint
                        const originalVector = Qt.vector2d(objectPicker.screenPoint.x - screenCenter2D.x, -(objectPicker.screenPoint.y - screenCenter2D.y))

                        // Compute the current vector screenCenter2D -> CurrentMousePoint
                        const mouseVector = Qt.vector2d(mouseHandler.currentPosition.x - screenCenter2D.x, -(mouseHandler.currentPosition.y - screenCenter2D.y))

                        // Get the angle from the originalVector to the mouseVector
                        const angle = Math.atan2(-originalVector.y*mouseVector.x + originalVector.x*mouseVector.y, originalVector.x*mouseVector.x + originalVector.y*mouseVector.y) * 180 / Math.PI

                        // Get the orientation of the gizmo in function of the camera
                        const gizmoLocalAxisVector = gizmoDisplayTransform.matrix.times(Qt.vector4d(pickedAxis.x, pickedAxis.y, pickedAxis.z, 0))
                        const gizmoToCameraVector = camera.position.toVector4d().minus(gizmoCenterPoint)
                        const orientation = gizmoLocalAxisVector.dotProduct(gizmoToCameraVector) > 0 ? 1 : -1

                        if (angle !== 0) doRotation(objectPicker.decomposedObjectModelMat, pickedAxis, angle*orientation)
                        return
                    }

                    case TransformGizmo.Type.SCALE: {
                        const sensibility = 0.05

                        // Get Screen Coordinates of the gizmo center
                        const gizmoCenterPoint = gizmoDisplayTransform.matrix.times(Qt.vector4d(0, 0, 0, 1))
                        const screenCenter2D = pointFromWorldToScreen(gizmoCenterPoint, camera, root.windowSize)

                        // Compute the scale unit
                        const scaleUnit = screenCenter2D.minus(Qt.vector2d(objectPicker.screenPoint.x, objectPicker.screenPoint.y)).length()

                        // Compute the current vector screenCenter2D -> CurrentMousePoint
                        const mouseVector = Qt.vector2d(mouseHandler.currentPosition.x - screenCenter2D.x, -(mouseHandler.currentPosition.y - screenCenter2D.y))
                        let offset = (mouseVector.length() - scaleUnit) * sensibility
                        offset = (offset < 0) ? offset * 3 : offset // Used to make it more sensible when we want to reduce the scale (because the action field is shorter)

                        if (offset) doScale(objectPicker.decomposedObjectModelMat, pickedAxis.times(offset))
                        return
                    }
                }
            }
        }
    }
}
