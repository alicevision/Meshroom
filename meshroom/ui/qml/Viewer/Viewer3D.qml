import QtQuick 2.7
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import QtQuick.Scene3D 2.0
import Qt3D.Core 2.1
import Qt3D.Render 2.1
import Qt3D.Input 2.1 as Qt3DInput // to avoid clash with Controls2 Action


FocusScope {
    id: root

    property alias status: scene.status
    property alias source: modelLoader.source
    readonly property alias loading: modelLoader.loading

    // functions
    function resetCameraCenter() {
        mainCamera.viewCenter = Qt.vector3d(0.0, 0.0, 0.0);
        mainCamera.upVector = Qt.vector3d(0.0, 1.0, 0.0);
    }

    function resetCameraPosition() {
        mainCamera.position = Qt.vector3d(28.0, 21.0, 28.0);
        mainCamera.upVector = Qt.vector3d(0.0, 1.0, 0.0);
        mainCamera.viewCenter = Qt.vector3d(0.0, 0.0, 0.0);
    }

    function findChildrenByProperty(node, propertyName, container)
    {
        if(!node || !node.childNodes)
            return;
        for(var i=0; i < node.childNodes.length; ++i)
        {
            var childNode = node.childNodes[i];
            if(!childNode)
                continue;
            if(childNode[propertyName] !== undefined)
                container.push(childNode);
            else
                findChildrenByProperty(childNode, propertyName, container)
        }
    }

    // Remove automatically created DiffuseMapMaterial and
    // instantiate a MaterialSwitcher instead
    function setupMaterialSwitchers(rootEntity)
    {
        var materials = [];
        findChildrenByProperty(rootEntity, "diffuse", materials);
        var entities = []
        materials.forEach(function(mat){
            entities.push(mat.parent)
        })

        entities.forEach(function(entity) {
            var comps = [];
            var mats = []
            for(var i=0; i < entity.components.length; ++i)
            {
                var comp = entity.components[i]
                // handle DiffuseMapMaterials created by SceneLoader
                if(comp.toString().indexOf("QDiffuseMapMaterial") > -1)
                {
                    // store material definition
                    var m = {
                        "diffuseMap": comp.diffuse.data[0].source,
                        "shininess": comp.shininess,
                        "specular": comp.specular,
                        "ambient": comp.ambient,
                        "showTextures": texturesCheckBox.checked
                    }
                    mats.push(m)
                    // unparent previous material
                    // and exclude it from the entity components
                    comp.parent = null
                }
                else
                    comps.push(comp)
            }
            entity.components = comps
            mats.forEach(function(m){
                // create a material switcher for each material definition
                var matSwitcher = materialSwitcherComponent.createObject(entity, m)
                // bind textures checkbox to texture switch property
                matSwitcher.showTextures = Qt.binding(function(){ return texturesCheckBox.checked })
            })
        })
    }

    Component {
        id: materialSwitcherComponent
        MaterialSwitcher {}
    }

    function clear()
    {
        source = 'no_file'
    }

    Scene3D {
        id: scene3D
        anchors.fill: parent
        cameraAspectRatioMode: Scene3D.AutomaticAspectRatio // vs. UserAspectRatio
        hoverEnabled: false // if true, will trigger positionChanged events in attached MouseHandler
        aspects: ["logic", "input"]
        focus: true

        Keys.onPressed: {
            if (event.key == Qt.Key_F) {
                resetCameraCenter();
                resetCameraPosition();
                event.accepted = true;
            }
        }

        Entity {
            id: rootEntity

            Camera {
                id: mainCamera
                projectionType: CameraLens.PerspectiveProjection
                fieldOfView: 45
                nearPlane : 0.1
                farPlane : 1000.0
                position: Qt.vector3d(28.0, 21.0, 28.0)
                upVector: Qt.vector3d(0.0, 1.0, 0.0)
                viewCenter: Qt.vector3d(0.0, 0.0, 0.0)
                aspectRatio: width/height

                Behavior on viewCenter {
                    Vector3dAnimation { duration: 250 }
                }
            }

            DefaultCameraController {
                id: cameraController
                camera: mainCamera
                onMousePressed: {
                    scene3D.forceActiveFocus()
                    if(mouse.button == Qt.LeftButton)
                    {
                        if(!doubleClickTimer.running)
                            doubleClickTimer.restart()
                    }
                    else
                        doubleClickTimer.stop()
                }
                onMouseReleased: {
                    if(moving)
                        return
                    if(mouse.button == Qt.RightButton)
                    {
                        contextMenu.popup()
                    }
                }

                // Manually handle double click to activate object picking
                // for camera re-centering only during a short amount of time
                Timer {
                    id: doubleClickTimer
                    running: false
                    interval: 300
                }
            }

            components: [
                RenderSettings {
                    // To avoid performance drops, picking is only enabled under certain circumstances (see ObjectPicker below)
                    pickingSettings.pickMethod: PickingSettings.TrianglePicking
                    pickingSettings.pickResultMode: PickingSettings.NearestPick
                    renderPolicy: RenderSettings.Always
                    activeFrameGraph: Viewport {
                        normalizedRect: Qt.rect(0.0, 0.0, 1.0, 1.0)
                        RenderSurfaceSelector {
                            CameraSelector {
                                id: cameraSelector
                                camera: mainCamera
                                ClearBuffers {
                                    buffers : ClearBuffers.ColorDepthBuffer
                                    clearColor: Qt.rgba(0, 0, 0, 0.1)
                                }
                            }
                        }
                    }
                },
                Qt3DInput.InputSettings {
                    eventSource: _window
                    enabled: true
                }
            ]

            Entity {
                id: modelLoader
                property string source
                // SceneLoader status is not reliable when loading a 3D file
                property bool loading
                onSourceChanged: loading = true

                components: [scene, transform, picker]

                // ObjectPicker used for view re-centering
                ObjectPicker {
                    id: picker
                    // Triangle picking is expensive
                    // Only activate it when a double click may happen or when the 'Control' key is pressed
                    enabled: cameraController.controlPressed || doubleClickTimer.running
                    hoverEnabled: false
                    onPressed: {
                        if(pick.button == Qt.LeftButton)
                            mainCamera.viewCenter = pick.worldIntersection
                        doubleClickTimer.stop()
                    }
                }

                Transform {
                    id: transform
                }

                SceneLoader {
                    id: scene
                    source: Qt.resolvedUrl(modelLoader.source)
                    onStatusChanged: {
                        if(scene.status != SceneLoader.Loading)
                            modelLoader.loading = false;
                        if(scene.status == SceneLoader.Ready)
                        {
                            setupMaterialSwitchers(parent)
                        }
                    }
                }
                Locator3D { enabled: locatorCheckBox.checked }
            }
            Grid3D { enabled: gridCheckBox.checked }

        }
    }

    Pane {
        background: Rectangle { color: palette.base; opacity: 0.5; radius: 2 }
        Column {
            spacing: 5            
            Row {
                spacing: 4
                Slider { width: 100; from: -180; to: 180; onPositionChanged: transform.rotationX = value}
                Label { text: "RX" }
            }

            Row {
                spacing: 4
                Slider { width: 100; from: -180; to: 180; onPositionChanged: transform.rotationY = value }
                Label { text: "RY" }
            }

            Row {
                spacing: 4
                Slider { width: 100; from: -180; to: 180; onPositionChanged: transform.rotationZ = value }
                Label { text: "RZ" }
            }

            Row {
                spacing: 4
                Slider { width: 100; from: 1; to: 10; onPositionChanged: transform.scale = value }
                Label { text: "Scale" }
            }
        }
    }

    Pane {
        background: Rectangle { color: palette.base; opacity: 0.5; radius: 2 }
        anchors.right: parent.right
        Column {
            CheckBox { id: gridCheckBox; text: "Grid"; checked: true }
            CheckBox { id: locatorCheckBox; text: "Locator"; checked: true }
            CheckBox { id: texturesCheckBox; text: "Textures"; checked: true }
        }
    }

    // Menu
    Menu {
        id: contextMenu
        MenuItem {
            text: "View All"
            onTriggered: mainCamera.viewAll()
        }
        MenuItem {
            text: "Reset View"
            onTriggered: resetCameraPosition()
        }
    }
}
