import Qt3D.Core 2.0
import Qt3D.Render 2.9
import Qt3D.Input 2.0
import Qt3D.Extras 2.9
import QtQuick 2.0

/**
 * MaterialSwitcher is an Entity that can change its parent's material
 * according to a set of property it exposes.
 * It can be used to toggle between a Phong and a DiffuseMapColor
 * depending on 'showTextures' value.
 */
Entity {
    id: root
    objectName: "MaterialSwitcher"

    property bool showTextures: true
    property string diffuseMap: ""
    property color ambient: "#AAA"
    property real shininess
    property color specular
    property color diffuseColor: "#AAA"
    property alias object: instantiator.object

    NodeInstantiator {
        id: instantiator

        delegate: root.showTextures ? textured : colored

        // add the created Node delegate to the root's parent components
        onObjectAdded: {
            if(!root.parent)
                return
            var comps = [];
            for(var i=0; i < root.parent.components.length; ++i)
            {
                comps.push(root.parent.components[i]);
            }
            comps.push(object);
            root.parent.components = comps;
        }
        // remove the created Node delegate from the root's parent components
        onObjectRemoved: {
            if(!root.parent)
                return
            var comps = [];
            for(var i=0; i < root.parent.components.length; ++i)
            {
                if(object != root.parent.components[i])
                    comps.push(root.parent.components[i]);
            }
            root.parent.components = comps;
        }
    }

    Component {
        id: colored
        PhongMaterial {
            parent: root.parent
            objectName: "DiffuseColorMaterial"
            ambient: root.ambient
            diffuse: root.diffuseColor
            shininess: root.shininess
            specular: root.specular
        }
    }

    Component {
        id: textured
        DiffuseMapMaterial {
            parent: root.parent
            objectName: "DiffuseMapMaterial"
            ambient: root.ambient
            shininess: root.shininess
            specular: root.specular

            diffuse: TextureLoader {
                id: baseColorLoader
                mirrored: false
                source: root.diffuseMap
                magnificationFilter: Texture.Linear
            }
        }
    }
}
