import Qt3D.Core 2.0
import Qt3D.Render 2.9
import Qt3D.Input 2.0
import Qt3D.Extras 2.10
import QtQuick 2.9
import Qt3D.Logic 2.0
import QtQuick.Controls 2.3
import Utils 1.0

Entity {
    id: root
    property real gizmoScale: 0.15
    property Camera camera
    property var windowSize
    property var frontLayerComponent
    property var window

    readonly property Transform objectTransform : Transform {
        translation: gizmoDisplayTransform.translation
        rotation: gizmoDisplayTransform.rotation
        scale3D: Qt.vector3d(1,1,1)
    }
    readonly property var updateTransformations: function updateTransformations(translation, rotation, scale) {
        const gizmoModelMat = Transformations3DHelper.computeModelMatrixWithEuler(translation, rotation, Qt.vector3d(1,1,1))
        gizmoDisplayTransform.setMatrix(gizmoModelMat) // Update gizmo matrix and translation/rotation of the object (with binding)
        objectTransform.scale3D = scale // Update the scale of the object
    }
    
    signal pickedChanged(bool pressed)
    signal gizmoChanged(var translation, var rotation, var scale)

    function emitGizmoChanged() {
        const translation = gizmoDisplayTransform.translation // Position in space
        const rotation = Qt.vector3d(gizmoDisplayTransform.rotationX, gizmoDisplayTransform.rotationY, gizmoDisplayTransform.rotationZ) // Euler angles
        const scale = objectTransform.scale3D // Scale of the object

        updateTransformations(translation, rotation, scale) // Optional: just to make sure the absolute values work well
        gizmoChanged(translation, rotation, scale)
    }

    components: [gizmoDisplayTransform, mouseHandler, frontLayerComponent]


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

    /***** TRANSFORMATIONS (using local vars) *****/

    function doRelativeTranslation(initialModelMatrix, translateVec) {
        Transformations3DHelper.relativeLocalTranslate(gizmoDisplayTransform, initialModelMatrix.position, initialModelMatrix.rotation, initialModelMatrix.scale, translateVec) // Update gizmo matrix and object matrix with binding
    }

    function doRelativeRotation(initialModelMatrix, axis, degree) {
        Transformations3DHelper.relativeLocalRotate(gizmoDisplayTransform, initialModelMatrix.position, initialModelMatrix.quaternion, initialModelMatrix.scale, axis, degree) // Update gizmo matrix and object matrix with binding
    }

    function doRelativeScale(initialModelMatrix, scaleVec) {
        Transformations3DHelper.relativeLocalScale(objectTransform, initialModelMatrix.position, initialModelMatrix.rotation, initialModelMatrix.scale, scaleVec) // Update only object matrix
    }

    function resetTranslation() {
        gizmoDisplayTransform.translation = Qt.vector3d(0,0,0) // Reset gizmo matrix and object matrix with binding
    }

    function resetRotation() {
        gizmoDisplayTransform.rotation = Qt.quaternion(1,0,0,0) // Reset gizmo matrix and object matrix with binding
    }

    function resetScale() {
        objectTransform.scale3D = Qt.vector3d(1,1,1) // Reset only object matrix
    }

    function resetATransformType(transformType) {
        switch(transformType) {
            case TransformGizmo.Type.POSITION: resetTranslation(); break
            case TransformGizmo.Type.ROTATION: resetRotation(); break
            case TransformGizmo.Type.SCALE: resetScale(); break
        }
        emitGizmoChanged()
    }

    /***** DEVICES *****/

    MouseDevice { id: mouseSourceDevice }

    MouseHandler {
        id: mouseHandler
        sourceDevice: enabled ? mouseSourceDevice : null
        property var objectPicker: null
        property bool enabled: false

        onPositionChanged: {
            if (objectPicker && objectPicker.button === Qt.LeftButton) {
                // Get the selected axis
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
                        const mouseVector = Qt.vector2d(mouse.x - pickedPosition.x, -(mouse.y - pickedPosition.y))

                        // Transform the positive picked axis vector from World Coord to Screen Coord
                        const gizmoLocalPointOnAxis = gizmoDisplayTransform.matrix.times(Qt.vector4d(pickedAxis.x, pickedAxis.y, pickedAxis.z, 1))
                        const gizmoCenterPoint = gizmoDisplayTransform.matrix.times(Qt.vector4d(0, 0, 0, 1))
                        const screenPoint2D = Transformations3DHelper.pointFromWorldToScreen(gizmoLocalPointOnAxis, camera, windowSize)
                        const screenCenter2D = Transformations3DHelper.pointFromWorldToScreen(gizmoCenterPoint, camera, windowSize)
                        const screenAxisVector = Qt.vector2d(screenPoint2D.x - screenCenter2D.x, -(screenPoint2D.y - screenCenter2D.y))

                        // Get the cosinus of the angle from the screenAxisVector to the mouseVector
                        const cosAngle = screenAxisVector.dotProduct(mouseVector) / (screenAxisVector.length() * mouseVector.length())
                        const offset = cosAngle * mouseVector.length() * sensibility

                        // If the mouse is not at the same spot as the pickedPoint, we do translation
                        if (offset) doRelativeTranslation(objectPicker.modelMatrix, pickedAxis.times(offset)) // Do a translation from the initial Object Model Matrix when we picked the gizmo

                        return
                    }

                    case TransformGizmo.Type.ROTATION: {
                        // Get Screen Coordinates of the gizmo center
                        const gizmoCenterPoint = gizmoDisplayTransform.matrix.times(Qt.vector4d(0, 0, 0, 1))
                        const screenCenter2D = Transformations3DHelper.pointFromWorldToScreen(gizmoCenterPoint, camera, root.windowSize)

                        // Get the vector screenCenter2D -> PickedPoint
                        const originalVector = Qt.vector2d(objectPicker.screenPoint.x - screenCenter2D.x, -(objectPicker.screenPoint.y - screenCenter2D.y))

                        // Compute the current vector screenCenter2D -> CurrentMousePoint
                        const mouseVector = Qt.vector2d(mouse.x - screenCenter2D.x, -(mouse.y - screenCenter2D.y))

                        // Get the angle from the originalVector to the mouseVector
                        const angle = Math.atan2(-originalVector.y*mouseVector.x + originalVector.x*mouseVector.y, originalVector.x*mouseVector.x + originalVector.y*mouseVector.y) * 180 / Math.PI

                        // Get the orientation of the gizmo in function of the camera
                        const gizmoLocalAxisVector = gizmoDisplayTransform.matrix.times(Qt.vector4d(pickedAxis.x, pickedAxis.y, pickedAxis.z, 0))
                        const gizmoToCameraVector = camera.position.toVector4d().minus(gizmoCenterPoint)
                        const orientation = gizmoLocalAxisVector.dotProduct(gizmoToCameraVector) > 0 ? 1 : -1

                        if (angle !== 0) doRelativeRotation(objectPicker.modelMatrix, pickedAxis, angle*orientation) // Do a rotation from the initial Object Model Matrix when we picked the gizmo

                        return
                    }

                    case TransformGizmo.Type.SCALE: {
                        const sensibility = 0.05

                        // Get Screen Coordinates of the gizmo center
                        const gizmoCenterPoint = gizmoDisplayTransform.matrix.times(Qt.vector4d(0, 0, 0, 1))
                        const screenCenter2D = Transformations3DHelper.pointFromWorldToScreen(gizmoCenterPoint, camera, root.windowSize)

                        // Compute the scale unit
                        const scaleUnit = screenCenter2D.minus(Qt.vector2d(objectPicker.screenPoint.x, objectPicker.screenPoint.y)).length()

                        // Compute the current vector screenCenter2D -> CurrentMousePoint
                        const mouseVector = Qt.vector2d(mouse.x - screenCenter2D.x, -(mouse.y - screenCenter2D.y))
                        let offset = (mouseVector.length() - scaleUnit) * sensibility
                        offset = (offset < 0) ? offset * 3 : offset // Used to make it more sensible when we want to reduce the scale (because the action field is shorter)

                        if (offset) doRelativeScale(objectPicker.modelMatrix, pickedAxis.times(offset)) // Do a scale from the initial Object Model Matrix when we picked the gizmo
                        
                        return
                    }
                }
            }

            if(objectPicker && objectPicker.button === Qt.RightButton) {
                resetMenu.updateTypeBeforePopup(objectPicker.gizmoType)
                resetMenu.popup(window)
            }
        }
        onReleased: {
            if(objectPicker && mouse.button === Qt.LeftButton) {
                emitGizmoChanged()
            }
        }
    }

    Menu {
        id: resetMenu
        property int transformType
        property string transformTypeToDisplay

        function updateTypeBeforePopup(type) {
            resetMenu.transformType = type
            switch(type) {
                case TransformGizmo.Type.POSITION: resetMenu.transformTypeToDisplay = "position"; break
                case TransformGizmo.Type.ROTATION: resetMenu.transformTypeToDisplay = "rotation"; break
                case TransformGizmo.Type.SCALE: resetMenu.transformTypeToDisplay = "scale"; break
            }    
        }

        MenuItem {
            text: `Reset ${resetMenu.transformTypeToDisplay}?`
            onTriggered: resetATransformType(resetMenu.transformType)
        }
    }

    /***** GIZMO'S BASIC COMPONENTS *****/

    Transform {
        id: gizmoDisplayTransform
        scale: root.gizmoScale * (camera.position.minus(gizmoDisplayTransform.translation)).length()
    }

    Entity {
        id: centerSphereEntity
        components: [centerSphereMesh, centerSphereMaterial, frontLayerComponent]

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
                    components: [cylinderMesh, cylinderTransform, scaleMaterial, frontLayerComponent]

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
                    components: [cubeScaleMesh, cubeScaleTransform, scaleMaterial, scalePicker, frontLayerComponent]

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
                        this.modelMatrix = Transformations3DHelper.modelMatrixToMatrices(objectTransform.matrix) // Save the current transformations
                        root.pickedChanged(picker.isPressed) // Used to prevent camera transformations
                    }
                }
            }

            // POSITION ENTITY
            Entity {
                id: positionEntity
                components: [coneMesh, coneTransform, positionMaterial, positionPicker, frontLayerComponent]

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
                        // this.modelMatrix = copyMatrix(objectTransform.matrix) // Save the current transformations
                        this.modelMatrix = Transformations3DHelper.modelMatrixToMatrices(objectTransform.matrix) // Save the current transformations
                        root.pickedChanged(picker.isPressed) // Used to prevent camera transformations
                    }
                }
            }

            // ROTATION ENTITY
            Entity {
                id: rotationEntity
                components: [torusMesh, torusTransform, rotationMaterial, rotationPicker, frontLayerComponent]

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
                        this.modelMatrix = Transformations3DHelper.modelMatrixToMatrices(objectTransform.matrix) // Save the current transformations
                        root.pickedChanged(picker.isPressed) // Used to prevent camera transformations
                    }
                }
            }
        }
    }
}
