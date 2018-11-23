import Qt3D.Core 2.0
import Qt3D.Render 2.9
import Qt3D.Input 2.0
import Qt3D.Extras 2.10
import QtQuick 2.0
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
            // remove previous material(s)
            removeComponentsByType(parent, "Material")
            addComponent(root.parent, material)
        }
    }

    function printComponents(entity)
    {
        console.log("Components of Entity '" + entity + "'")
        for(var i=0; i < entity.components.length; ++i)
        {
            console.log(" -- [" + i + "]: " + entity.components[i])
        }
    }

    function addComponent(entity, component)
    {
        if(!entity)
            return
        var comps = [];
        comps.push(component);

        for(var i=0; i < entity.components.length; ++i)
        {
            comps.push(entity.components[i]);
        }
        entity.components = comps;
    }

    function removeComponentsByType(entity, type)
    {
        if(!entity)
            return
        var comps = [];
        for(var i=0; i < entity.components.length; ++i)
        {
            if(entity.components[i].toString().indexOf(type) == -1)
            {
                comps.push(entity.components[i]);
            }
        }
        entity.components = comps;
    }

    function removeComponent(entity, component)
    {
        if(!entity)
            return
        var comps = [];

        for(var i=0; i < entity.components.length; ++i)
        {
            if(entity.components[i] == component)
            {
                comps.push(entity.components[i]);
            }
        }
        entity.components = comps;
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
                PropertyChanges { target: m; material: diffuseMap ? textured : solid }
            }
        ]
    }

    // Solid and Textured modes could and should be using the same material
    // but get random shader errors (No shader program found for DNA)
    // when toggling between a color and a texture for the diffuse property

    DiffuseSpecularMaterial {
        id: solid
        parent: root.parent
        objectName: "SolidMaterial"
        ambient: root.ambient
        shininess: root.shininess
        specular: root.specular
        diffuse: root.diffuseColor
    }

    DiffuseSpecularMaterial {
        id: textured
        parent: root.parent
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
        parent: root.parent
        objectName: "WireframeMaterial"
        effect: WireframeEffect {}
        ambient: root.ambient
        diffuse: root.diffuseColor
        shininess: 0
        specular: root.specular
    }

}
