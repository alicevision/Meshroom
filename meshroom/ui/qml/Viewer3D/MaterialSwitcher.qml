import Qt3D.Core 2.6
import Qt3D.Render 2.6
import Qt3D.Input 2.6
import Qt3D.Extras 2.15
import QtQuick

import Utils 1.0
import "Materials"

/**
 * MaterialSwitcher is an Entity that can change its parent's material
 * by setting the 'mode' property.
 */

Entity {
    id: root
    objectName: "MaterialSwitcher"

    property int mode: 2
    property string diffuseMap: ""
    property color ambient: "#AAA"
    property real shininess
    property color specular
    property color diffuseColor: "#AAA"

    readonly property alias activeMaterial: m.material

    QtObject {
        id: m
        property Material material
        onMaterialChanged: {
            // Remove previous material(s)
            removeComponentsByType(parent, "Material")
            Scene3DHelper.addComponent(root.parent, material)
        }
    }

    function removeComponentsByType(entity, type)
    {
        if (!entity)
            return
        for (var i = 0; i < entity.components.length; ++i) {
            if (entity.components[i].toString().indexOf(type) !== -1) {
                Scene3DHelper.removeComponent(entity, entity.components[i])
            }
        }
    }

    StateGroup {
        id: modeState
        state: Viewer3DSettings.renderModes[mode].name

        states: [
            State {
                name: "Solid"
                PropertyChanges { target: m; material: solid }
            },
            State {
                name: "Wireframe"
                PropertyChanges { target: m; material: wireframe }
            },
            State {
                name: "Textured"
                PropertyChanges {
                    target: m;
                    // "textured" material resolution order: diffuse map > vertex color data >  no color info
                    material: diffuseMap ? textured : (Scene3DHelper.vertexColorCount(root.parent) ? colored : solid)
                }
            },
            State {
                name: "Spherical Harmonics"
                PropertyChanges { target: m; material: shMaterial }
            }
        ]
    }

    // Solid and Textured modes could and should be using the same material
    // but get random shader errors (No shader program found for DNA)
    // when toggling between a color and a texture for the diffuse property

    DiffuseSpecularMaterial {
        id: solid
        objectName: "SolidMaterial"
        ambient: root.ambient
        shininess: root.shininess
        specular: root.specular
        diffuse: root.diffuseColor
    }

    PerVertexColorMaterial {
        id: colored
        objectName: "VertexColorMaterial"
    }

    DiffuseMapMaterial {
        id: textured
        objectName: "TexturedMaterial"
        ambient: root.ambient
        shininess: root.shininess
        specular: root.specular
        diffuse: TextureLoader {
            magnificationFilter: Texture.Linear
            mirrored: false
            source: diffuseMap
        }
    }

    WireframeMaterial {
        id: wireframe
        objectName: "WireframeMaterial"
        effect: WireframeEffect {}
    }

    SphericalHarmonicsMaterial {
        id: shMaterial
        objectName: "SphericalHarmonicsMaterial"
        effect: SphericalHarmonicsEffect {}
        shlSource: Filepath.stringToUrl(Viewer3DSettings.shlFile)
        displayNormals: Viewer3DSettings.displayNormals
    }
}
