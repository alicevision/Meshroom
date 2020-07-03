import Qt3D.Core 2.0
import Qt3D.Render 2.9
import Qt3D.Input 2.0
import Qt3D.Extras 2.10
import QtQuick 2.9
import Qt3D.Logic 2.0

Entity {
    id: root
    property real gizmoScale: 0.15
    property Camera camera

    components: [gizmoTransform]

    enum Axis {
        X,
        Y,
        Z
    }

    Transform {
        id: gizmoTransform
        scale: {
            return root.gizmoScale * (camera.position.minus(gizmoTransform.translation)).length()
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

            PhongMaterial {
                id: material
                ambient: baseColor
                shininess: 0.2
            }

            // SCALE ENTITY
            Entity {
                id: scaleEntity
                components: [material]

                Entity {
                    id: axisCylinder
                    components: [cylinderMesh, cylinderTransform, material]

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
                    components: [cubeScaleMesh, cubeScaleTransform, material]

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
            }

            // POSITION ENTITY
            Entity {
                id: positionEntity
                components: [coneMesh, coneTransform, material]

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
            }

            // ROTATION ENTITY
            Entity {
                id: rotationEntity
                components: [torusMesh, torusTransform, material]

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
            }
        }
    }
}
