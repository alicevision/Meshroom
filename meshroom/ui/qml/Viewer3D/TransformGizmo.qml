import Qt3D.Core 2.6
import Qt3D.Render 2.6
import Qt3D.Input 2.6
import Qt3D.Extras 2.15
import Qt3D.Logic 2.6
import QtQuick
import QtQuick.Controls

import Utils 1.0

/**
 * Simple transformation gizmo entirely made with Qt3D entities.
 * Uses Python Transformations3DHelper to compute matrices.
 * This TransformGizmo entity should only be instantiated in EntityWithGizmo entity which is its wrapper.
 * It means, to use it for a specified application, make sure to instantiate EntityWithGizmo.
 */

Entity {
    id: root
    property Camera camera
    property var windowSize
    property Layer frontLayerComponent  // Used to draw gizmo on top of everything
    property var window
    readonly property alias gizmoScale: gizmoScaleLookSlider.value
    property bool uniformScale: false  // By default, the scale is not uniform
    property bool focusGizmoPriority: false  // If true, it is used to give the priority to the current transformation (and not to a upper-level binding)
    property Transform gizmoDisplayTransform: Transform {
        id: gizmoDisplayTransform
        scale: root.gizmoScale * (camera.position.minus(gizmoDisplayTransform.translation)).length()  // The gizmo needs a constant apparent size
    }
    // Component the object controlled by the gizmo must use
    property Transform objectTransform : Transform {
        translation: gizmoDisplayTransform.translation
        rotation: gizmoDisplayTransform.rotation
        scale3D: Qt.vector3d(1,1,1)
    }
    
    signal pickedChanged(bool pressed)
    signal gizmoChanged(var translation, var rotation, var scale, int type)

    function emitGizmoChanged(type) {
        const translation = gizmoDisplayTransform.translation  // Position in space
        const rotation = Qt.vector3d(gizmoDisplayTransform.rotationX, gizmoDisplayTransform.rotationY, gizmoDisplayTransform.rotationZ) // Euler angles
        const scale = objectTransform.scale3D // Scale of the object

        gizmoChanged(translation, rotation, scale, type)
        root.focusGizmoPriority = false
    }

    components: [gizmoDisplayTransform, mouseHandler, frontLayerComponent]


    /***** ENUMS *****/

    enum Axis {
        X,
        Y,
        Z
    }

    enum Direction {
        Forward,
        Backward
    }

    enum Type {
        TRANSLATION,
        ROTATION,
        SCALE,
        ALL
    }

    function convertAxisEnum(axis) {
        switch (axis) {
            case TransformGizmo.Axis.X: return Qt.vector3d(1,0,0)
            case TransformGizmo.Axis.Y: return Qt.vector3d(0,1,0)
            case TransformGizmo.Axis.Z: return Qt.vector3d(0,0,1)
        }
    }

    function convertDirectionEnum(direction) {
        switch (direction) {
            case TransformGizmo.Direction.Forward: return 1
            case TransformGizmo.Direction.Backward: return -1
        }
    }

    function convertTypeEnum(type) {
        switch (type) {
            case TransformGizmo.Type.TRANSLATION: return "TRANSLATION"
            case TransformGizmo.Type.ROTATION: return "ROTATION"
            case TransformGizmo.Type.SCALE: return "SCALE"
            case TransformGizmo.Type.ALL: return "ALL"
        }
    }

    /***** TRANSFORMATIONS (using local vars) *****/

    /**
     * @brief Translate locally the gizmo and the object.
     *
     * @remarks
     *      To make local translation, we need to recompute a new matrix.
     *      Update gizmoDisplayTransform's matrix and all its properties while avoiding the override of translation property.
     *      Update objectTransform in the same time thanks to binding on translation property.
     *
     * @param initialModelMatrix object containing position, rotation and scale matrices + rotation quaternion
     * @param translateVec vector3d used to make the local translation
     */
    function doRelativeTranslation(initialModelMatrix, translateVec) {
        Transformations3DHelper.relativeLocalTranslate(
            gizmoDisplayTransform,
            initialModelMatrix.position,
            initialModelMatrix.rotation,
            initialModelMatrix.scale,
            translateVec
        )
    }

    /**
     * @brief Rotate the gizmo and the object around a specific axis.
     *
     * @remarks
     *      To make local rotation around an axis, we need to recompute a new matrix from a quaternion.
     *      Update gizmoDisplayTransform's matrix and all its properties while avoiding the override of rotation, rotationX, rotationY and rotationZ properties.
     *      Update objectTransform in the same time thanks to binding on rotation property.
     *
     * @param initialModelMatrix object containing position, rotation and scale matrices + rotation quaternion
     * @param axis vector3d describing the axis to rotate around
     * @param degree angle of rotation in degrees
     */
    function doRelativeRotation(initialModelMatrix, axis, degree) {
        Transformations3DHelper.relativeLocalRotate(
            gizmoDisplayTransform,
            initialModelMatrix.position,
            initialModelMatrix.quaternion,
            initialModelMatrix.scale,
            axis,
            degree
        )
    }

    /**
     * @brief Scale the object relatively to its current scale.
     *
     * @remarks
     *      To change scale of the object, we need to recompute a new matrix to avoid overriding bindings.
     *      Update objectTransform properties only (gizmoDisplayTransform is not affected).
     *
     * @param initialModelMatrix object containing position, rotation and scale matrices + rotation quaternion
     * @param scaleVec vector3d used to make the relative scale
     */
    function doRelativeScale(initialModelMatrix, scaleVec) {
        Transformations3DHelper.relativeLocalScale(
            objectTransform,
            initialModelMatrix.position,
            initialModelMatrix.rotation,
            initialModelMatrix.scale,
            scaleVec
        )
    }

    /**
     * @brief Reset the translation of the gizmo and the object.
     *
     * @remarks
     *      Update gizmoDisplayTransform's matrix and all its properties while avoiding the override of translation property.
     *      Update objectTransform in the same time thanks to binding on translation property.
     */
    function resetTranslation() {
        const mat = gizmoDisplayTransform.matrix
        const newMat = Qt.matrix4x4(
            mat.m11, mat.m12, mat.m13, 0,
            mat.m21, mat.m22, mat.m23, 0,
            mat.m31, mat.m32, mat.m33, 0,
            mat.m41, mat.m42, mat.m43, 1
        )
        gizmoDisplayTransform.setMatrix(newMat)
    }

    /**
     * @brief Reset the rotation of the gizmo and the object.
     *
     * @remarks
     *      Update gizmoDisplayTransform's quaternion while avoiding the override of rotationX, rotationY and rotationZ properties.
     *      Update objectTransform in the same time thanks to binding on rotation property.
     *      Here, we can change the rotation property (but not rotationX, rotationY and rotationZ because they can be used in upper-level bindings).
     *
     * @note
     *      We could implement a way of changing the matrix instead of overriding rotation (quaternion) property.
     */
    function resetRotation() {
        gizmoDisplayTransform.rotation = Qt.quaternion(1,0,0,0)
    }

    /**
     * @brief Reset the scale of the object.
     *
     * @remarks
     *      To reset the scale, we make the difference of the current one to 1 and recompute the matrix.
     *      Like this, we kind of apply an inverse scale transformation.
     *      It prevents overriding scale3D property (because it can be used in upper-level binding).
     */
    function resetScale() {
        const modelMat = Transformations3DHelper.modelMatrixToMatrices(objectTransform.matrix)
        const scaleDiff = Qt.vector3d(
            -(objectTransform.scale3D.x - 1),
            -(objectTransform.scale3D.y - 1),
            -(objectTransform.scale3D.z - 1)
        )
        doRelativeScale(modelMat, scaleDiff)
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
                root.focusGizmoPriority = true

                // Get the selected axis
                const pickedAxis = convertAxisEnum(objectPicker.gizmoAxis)

                // TRANSLATION, SCALE or SURFACE MOVE transformation = SURFACE MOVE is a combination of TRANSLATION AND SCALE
                if (objectPicker.gizmoType === TransformGizmo.Type.TRANSLATION || objectPicker.gizmoType === TransformGizmo.Type.SCALE || objectPicker.gizmoType === TransformGizmo.Type.ALL) {
                    // Compute the vector PickedPosition -> CurrentMousePoint
                    const pickedPosition = objectPicker.screenPoint
                    const mouseVector = Qt.vector2d((mouse.x - pickedPosition.x), -(mouse.y - pickedPosition.y))


                    // Transform the positive picked axis vector from World Coord to Screen Coord
                    const gizmoLocalPointOnAxis = gizmoDisplayTransform.matrix.times(Qt.vector4d(pickedAxis.x, pickedAxis.y, pickedAxis.z, 1))
                    const gizmoCenterPoint = gizmoDisplayTransform.matrix.times(Qt.vector4d(0, 0, 0, 1))
                    const screenPoint2D = Transformations3DHelper.pointFromWorldToScreen(gizmoLocalPointOnAxis, camera, windowSize)
                    const screenCenter2D = Transformations3DHelper.pointFromWorldToScreen(gizmoCenterPoint, camera, windowSize)
                    const screenAxisVector = Qt.vector2d(screenPoint2D.x - screenCenter2D.x, -(screenPoint2D.y - screenCenter2D.y))

                    // Get the cosinus of the angle from the screenAxisVector to the mouseVector
                    // It will be used as a intensity factor
                    const cosAngle = screenAxisVector.dotProduct(mouseVector) / (screenAxisVector.length() * mouseVector.length())
                    const offset = cosAngle * mouseVector.length() / objectPicker.scaleUnit

                    // Do the transformation
                    if (objectPicker.gizmoType === TransformGizmo.Type.TRANSLATION && offset !== 0) {
                        doRelativeTranslation(objectPicker.modelMatrix, pickedAxis.times(offset))  // Do a translation from the initial Object Model Matrix when we picked the gizmo
                    } else if (objectPicker.gizmoType === TransformGizmo.Type.SCALE && offset !== 0) {
                        if (root.uniformScale)
                            doRelativeScale(objectPicker.modelMatrix, Qt.vector3d(1, 1, 1).times(offset))  // Do a uniform scale from the initial Object Model Matrix when we picked the gizmo
                        else
                            doRelativeScale(objectPicker.modelMatrix, pickedAxis.times(offset))  // Do a scale on one axis from the initial Object Model Matrix when we picked the gizmo
                    }

                    else if (objectPicker.gizmoType === TransformGizmo.Type.ALL && offset !== 0) {
                        const sign = convertDirectionEnum(objectPicker.gizmoDirection)
                        doRelativeScale(objectPicker.modelMatrix, pickedAxis.times(sign * offset/2))
                        doRelativeTranslation(objectPicker.modelMatrix, pickedAxis.times(offset/2))
                    }
                    return
                }
                // ROTATION transformation
                else if (objectPicker.gizmoType === TransformGizmo.Type.ROTATION) {
                    // Get Screen Coordinates of the gizmo center
                    const gizmoCenterPoint = gizmoDisplayTransform.matrix.times(Qt.vector4d(0, 0, 0, 1))
                    const screenCenter2D = Transformations3DHelper.pointFromWorldToScreen(gizmoCenterPoint, camera, root.windowSize)

                    // Get the vector screenCenter2D -> PickedPosition
                    const originalVector = Qt.vector2d(objectPicker.screenPoint.x - screenCenter2D.x, -(objectPicker.screenPoint.y - screenCenter2D.y))

                    // Compute the vector screenCenter2D -> CurrentMousePoint
                    const mouseVector = Qt.vector2d(mouse.x - screenCenter2D.x, -(mouse.y - screenCenter2D.y))

                    // Get the angle from the originalVector to the mouseVector
                    const angle = Math.atan2(-originalVector.y * mouseVector.x + originalVector.x * mouseVector.y, originalVector.x * mouseVector.x + originalVector.y * mouseVector.y) * 180 / Math.PI

                    // Get the orientation of the gizmo in function of the camera
                    const gizmoLocalAxisVector = gizmoDisplayTransform.matrix.times(Qt.vector4d(pickedAxis.x, pickedAxis.y, pickedAxis.z, 0))
                    const gizmoToCameraVector = camera.position.toVector4d().minus(gizmoCenterPoint)
                    const orientation = gizmoLocalAxisVector.dotProduct(gizmoToCameraVector) > 0 ? 1 : -1

                    if (angle !== 0)
                        doRelativeRotation(objectPicker.modelMatrix, pickedAxis, angle * orientation)  // Do a rotation from the initial Object Model Matrix when we picked the gizmo

                    return
                }
            }

            if (objectPicker && objectPicker.button === Qt.RightButton) {
                resetMenu.popup(window)
            }
        }
        onReleased: {
            if (objectPicker && mouse.button === Qt.LeftButton) {
                const type = objectPicker.gizmoType
                objectPicker = null  // To prevent going again in the onPositionChanged
                emitGizmoChanged(type)
            }
        }
    }

    Menu {
        id: resetMenu

        MenuItem {
            text: "Reset Translation"
            onTriggered: {
                resetTranslation()
                emitGizmoChanged(TransformGizmo.Type.TRANSLATION)
            }
        }
        MenuItem {
            text: "Reset Rotation"
            onTriggered: {
                resetRotation()
                emitGizmoChanged(TransformGizmo.Type.ROTATION)
            }
        }
        MenuItem {
            text: "Reset Scale"
            onTriggered: {
                resetScale()
                emitGizmoChanged(TransformGizmo.Type.SCALE)
            }
        }
        MenuItem {
            text: "Reset All"
            onTriggered: {
                resetTranslation()
                resetRotation()
                resetScale()
                emitGizmoChanged(TransformGizmo.Type.ALL)
            }
        }
        MenuItem {
            text: "Gizmo Scale Look"
            Slider {
                id: gizmoScaleLookSlider
                anchors.right: parent.right
                anchors.rightMargin: 10
                height: parent.height
                width: parent.width * 0.40

                from: 0.06
                to: 0.30
                stepSize: 0.01
                value: 0.15
            }
        }
    }

    /***** GIZMO'S BASIC COMPONENTS *****/

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
                switch (index) {
                    case 0: return TransformGizmo.Axis.X
                    case 1: return TransformGizmo.Axis.Y
                    case 2: return TransformGizmo.Axis.Z
                }                
            }
            property color baseColor: {
                switch (axis) {
                    case TransformGizmo.Axis.X: return "#e63b55"  // Red
                    case TransformGizmo.Axis.Y: return "#83c414"  // Green
                    case TransformGizmo.Axis.Z: return "#3387e2"  // Blue
                }
            }
            property real lineRadius: 0.011

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
                            const offset = cylinderMesh.length / 2 + centerSphereMesh.radius
                            const m = Qt.matrix4x4()
                            switch (axis) {
                                case TransformGizmo.Axis.X: {
                                    m.translate(Qt.vector3d(offset, 0, 0))
                                    m.rotate(90, Qt.vector3d(0, 0, 1))
                                    break
                                }   
                                case TransformGizmo.Axis.Y: {
                                    m.translate(Qt.vector3d(0, offset, 0))
                                    break
                                }
                                case TransformGizmo.Axis.Z: {
                                    m.translate(Qt.vector3d(0, 0, offset))
                                    m.rotate(90, Qt.vector3d(1, 0, 0))
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
                        property real edge: 0.06
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
                                    m.rotate(90, Qt.vector3d(0, 0, 1))
                                    break
                                }
                                case TransformGizmo.Axis.Y: {
                                    m.translate(Qt.vector3d(0, offset, 0))
                                    break
                                }
                                case TransformGizmo.Axis.Z: {
                                    m.translate(Qt.vector3d(0, 0, offset))
                                    m.rotate(90, Qt.vector3d(1, 0, 0))
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
                        // Save the current transformations of the OBJECT
                        this.modelMatrix = Transformations3DHelper.modelMatrixToMatrices(objectTransform.matrix)
                        // Compute a scale unit at picking time
                        this.scaleUnit = Transformations3DHelper.computeScaleUnitFromModelMatrix(convertAxisEnum(gizmoAxis), gizmoDisplayTransform.matrix, camera, root.windowSize)
                        // Prevent camera transformations
                        root.pickedChanged(picker.isPressed)
                    }
                }
            }

            // TRANSLATION ENTITY
            Entity {
                id: positionEntity
                components: [coneMesh, coneTransform, positionMaterial, positionPicker, frontLayerComponent]

                ConeMesh {
                    id: coneMesh
                    bottomRadius: 0.035
                    topRadius: 0.001
                    hasBottomEndcap: true
                    hasTopEndcap: true
                    length: 0.13
                    rings: 2
                    slices: 8
                }
                Transform {
                    id: coneTransform
                    matrix: {
                        const offset = cylinderMesh.length + centerSphereMesh.radius + 0.4
                        const m = Qt.matrix4x4()
                        switch (axis) {
                            case TransformGizmo.Axis.X: {
                                m.translate(Qt.vector3d(offset, 0, 0))
                                m.rotate(-90, Qt.vector3d(0, 0, 1))
                                break
                            }
                            case TransformGizmo.Axis.Y: {
                                m.translate(Qt.vector3d(0, offset, 0))
                                break
                            }
                            case TransformGizmo.Axis.Z: {
                                m.translate(Qt.vector3d(0, 0, offset))
                                m.rotate(90, Qt.vector3d(1, 0, 0))
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
                    gizmoType: TransformGizmo.Type.TRANSLATION

                    onPickedChanged: {
                        // Save the current transformations of the OBJECT
                        this.modelMatrix = Transformations3DHelper.modelMatrixToMatrices(objectTransform.matrix)
                        // Compute a scale unit at picking time
                        this.scaleUnit = Transformations3DHelper.computeScaleUnitFromModelMatrix(convertAxisEnum(gizmoAxis), gizmoDisplayTransform.matrix, camera, root.windowSize)
                        // Prevent camera transformations
                        root.pickedChanged(picker.isPressed)
                    }
                }
            }

            // MOVE SURFACE ENTITY INSTANTIATOR => Forward/Backward axis directions
            // The bounding box has 6 surfaces. Each of the three axes is pointing to a surface.
            // These three surfaces have "forward direction". The three othersurfaces have "backward direction".
            NodeInstantiator {
                model: 2
                active: !root.uniformScale  // Shouldn't be active for SfmTransform Gizmo node for example
                
                Entity {

                    property int direction : {
                        switch (index) {
                            case 0: return TransformGizmo.Direction.Forward
                            case 1: return TransformGizmo.Direction.Backward
                        }                
                    }

                    // MOVE SURFACE ENTITY
                    Entity {
                        id: surfaceMoveEntity
                        components: [surfaceMesh, surfaceTransform, surfaceMaterial, frontLayerComponent, surfacePicker]

                        SphereMesh {
                            id: surfaceMesh
                            radius: 0.04
                            rings: 8
                            slices: 8
                        }
                        Transform {
                            id: surfaceTransform
                            matrix: {
                                const m = Qt.matrix4x4()
                                const sign = convertDirectionEnum(direction)
                                const offset = 0.3
                                switch (axis) {
                                    case TransformGizmo.Axis.X: {
                                        m.translate(Qt.vector3d(sign * (objectTransform.scale3D.x + offset) / gizmoDisplayTransform.scale3D.x, 0, 0))
                                        m.rotate(-90, Qt.vector3d(0, 0, 1))
                                        break
                                    }

                                    case TransformGizmo.Axis.Y: {
                                        m.translate(Qt.vector3d(0, sign * (objectTransform.scale3D.y + offset) / gizmoDisplayTransform.scale3D.y, 0))
                                        break
                                    }
                                    case TransformGizmo.Axis.Z: {
                                        m.translate(Qt.vector3d(0, 0, sign * (objectTransform.scale3D.z + offset) / gizmoDisplayTransform.scale3D.z))
                                        m.rotate(90, Qt.vector3d(1, 0, 0))
                                        break
                                    }
                                }
                                return m
                            }
                        }
                        PhongMaterial {
                            id: surfaceMaterial
                            ambient: baseColor
                        }

                        TransformGizmoPicker { 
                            id: surfacePicker
                            mouseController: mouseHandler
                            gizmoMaterial: surfaceMaterial
                            gizmoBaseColor: baseColor
                            gizmoAxis: axis
                            gizmoType: TransformGizmo.Type.ALL
                            property var gizmoDirection: direction

                            onPickedChanged: {
                                // Save the current transformations of the OBJECT
                                this.modelMatrix = Transformations3DHelper.modelMatrixToMatrices(objectTransform.matrix)
                                // Compute a scale unit at picking time
                                this.scaleUnit = Transformations3DHelper.computeScaleUnitFromModelMatrix(convertAxisEnum(gizmoAxis), gizmoDisplayTransform.matrix, camera, root.windowSize)
                                // Prevent camera transformations
                                root.pickedChanged(picker.isPressed)
                            }
                        }
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
                        const scaleDiff = 2 * torusMesh.minorRadius + 0.01  // Just to make sure there is no face overlapping
                        const m = Qt.matrix4x4()
                        switch (axis) {
                            case TransformGizmo.Axis.X: m.rotate(90, Qt.vector3d(0, 1, 0)); break
                            case TransformGizmo.Axis.Y: m.rotate(90, Qt.vector3d(1, 0, 0)); m.scale(Qt.vector3d(1 - scaleDiff, 1 - scaleDiff, 1 - scaleDiff)); break
                            case TransformGizmo.Axis.Z: m.scale(Qt.vector3d(1 - 2 * scaleDiff, 1 - 2 * scaleDiff, 1 - 2 * scaleDiff)); break
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
                        // Save the current transformations of the OBJECT
                        this.modelMatrix = Transformations3DHelper.modelMatrixToMatrices(objectTransform.matrix)
                        // No need to compute a scale unit for rotation
                        // Prevent camera transformations
                        root.pickedChanged(picker.isPressed)
                    }
                }
            }
        }
    }
}
