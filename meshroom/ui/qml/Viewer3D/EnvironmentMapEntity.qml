import QtQuick
import Qt3D.Core 2.6
import Qt3D.Render 2.6
import Qt3D.Extras 2.15

/**
 * EnvironmentMap maps an equirectangular image on a Sphere.
 * The 'position' property can be used to virually attach it to a camera
 * and get the impression of an environment at an infinite distance.
 */

Entity {
    id: root

    /// Source of the equirectangular image
    property url source
    /// Radius of the sphere
    property alias radius: sphereMesh.radius
    /// Number of slices of the sphere
    property alias slices: sphereMesh.slices
    /// Number of rings of the sphere
    property alias rings: sphereMesh.rings
    /// Position of the sphere
    property alias position: transform.translation
    /// Texture loading status
    property alias status: textureLoader.status

    components: [
        SphereMesh {
            id: sphereMesh
            radius: 1000
            slices: 50
            rings: 50
        },
        Transform {
            id: transform
            translation: root.position
        },
        DiffuseMapMaterial {
            ambient: "#FFF"
            shininess: 0
            specular: "#000"
            diffuse: TextureLoader {
                id: textureLoader
                magnificationFilter: Texture.Linear
                mirrored: true
                source: root.source
            }
        }
    ]
}
