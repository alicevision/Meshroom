import Qt3D.Core 2.0
import Qt3D.Render 2.9
import Qt3D.Input 2.0
import Qt3D.Extras 2.10
import QtQuick 2.9

Entity {
    id: root
    property real beamRadius: 0.0075
    property real beamLength: 1
    property int slices: 10
    property int rings: 50
    property color colorX: "#F44336"
    property color colorY: "#8BC34A"
    property color colorZ: "#03A9F4"
    property real alpha: 1.0
    property Transform transform: Transform {}

    components: [transform]

    Behavior on alpha {
        PropertyAnimation { duration: 100 }
    }

    SystemPalette { id: sysPalette }

    // Gizmo center
    Entity {
        components: [
            SphereMesh { radius: beamRadius * 4},
            PhongMaterial {
                ambient: "#FFF"
                shininess: 0.2
                diffuse: sysPalette.highlight
                specular: sysPalette.highlight
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
                        switch(index) {
                            case 0: return colorX;
                            case 1: return colorY;
                            case 2: return colorZ;
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
