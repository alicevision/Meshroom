import Qt3D.Core 2.6
import Qt3D.Render 2.6
import Qt3D.Input 2.6
import Qt3D.Extras 2.15
import QtQuick

Entity {
    id: root
    property real beamRadius: 0.0075
    property real beamLength: 1
    property int slices: 10
    property int rings: 50
    property color centerColor: "white"
    property color xColor: "red"
    property color yColor: "green"
    property color zColor: "blue"
    property real alpha: 1.0
    property Transform transform: Transform {}

    components: [transform]

    Behavior on alpha {
        PropertyAnimation { duration: 100 }
    }

    // Gizmo center
    Entity {
        components: [
            SphereMesh { radius: beamRadius * 4},
            PhongMaterial {
                ambient: "#FFF"
                shininess: 0.2
                diffuse: centerColor
                specular: centerColor
            }
        ]
    }

    // X, Y, Z rings
    NodeInstantiator {
        model: 3
        Entity {
            components: [
                TorusMesh {
                    radius: root.beamLength
                    minorRadius: root.beamRadius
                    slices: root.slices
                    rings: root.rings
                },
                DiffuseSpecularMaterial {
                    ambient: {
                        switch (index) {
                            case 0: return xColor;
                            case 1: return yColor;
                            case 2: return zColor;
                        }
                    }
                    shininess: 0
                    diffuse: Qt.rgba(0.6, 0.6, 0.6, root.alpha)
                },

                Transform {
                    rotationY: index == 0 ? 90 : 0
                    rotationX: index == 1 ? 90 : 0
                }
            ]
        }
    }
}
