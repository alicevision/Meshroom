import Qt3D.Core 2.0
import Qt3D.Render 2.9
import Qt3D.Input 2.0
import Qt3D.Extras 2.10
import QtQuick 2.9

Entity {
    id: root
    property Transform transform: Transform {}
    components: [mesh, transform, material]

    CuboidMesh {
        id: mesh
        property real edge : 2 // Important to have all the cube's vertices with a unit of 1
        xExtent: edge
        yExtent: edge
        zExtent: edge
    }
    PhongAlphaMaterial {
        id: material
        property color base: "#dfe233"
        ambient: base
        alpha: 0.3
    }
}