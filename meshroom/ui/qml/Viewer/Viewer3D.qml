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

    function unmirrorTextures(rootEntity)
    {
        var materials = [];
        findChildrenByProperty(rootEntity, "diffuse", materials);

        var textures = [];
        materials.forEach(function(mat){
            mat["diffuse"].magnificationFilter = Texture.Linear;
            findChildrenByProperty(mat["diffuse"], "mirrored", textures)
        })

        //console.log(textures)
        textures.forEach(function(tex){
            //console.log("Unmirroring: " + tex.source)
            tex.mirrored = false
        })
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

            MayaCameraController {
                id: cameraController
                camera: mainCamera
                onMousePressed: {
                    mouse.accepted = false
                    scene3D.forceActiveFocus()
                }
                onMouseReleased: {
                    if(moving)
                        return;
                    switch(mouse.button) {
                        case Qt.LeftButton:
                            break;
                        case Qt.RightButton:
                            contextMenu.x = mouse.x;
                            contextMenu.y = mouse.y;
                            contextMenu.open();
                            break;
                    }
                }
            }

            components: [
                RenderSettings {
                    // To avoid performance drop, only pick triangles when not moving the camera
                    pickingSettings.pickMethod: cameraController.moving ? PickingSettings.BoundingVolumePicking : PickingSettings.TrianglePicking
                    renderPolicy: RenderSettings.Always
                    activeFrameGraph: Viewport {
                        normalizedRect: Qt.rect(0.0, 0.0, 1.0, 1.0)
                        RenderSurfaceSelector {
                            CameraSelector {
                                id: cameraSelector
                                camera: mainCamera
                                //FrustumCulling {
                                    ClearBuffers {
                                        buffers : ClearBuffers.ColorDepthBuffer
                                        clearColor: Qt.rgba(0, 0, 0, 0.1)
                                    }
                                //}
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

                ObjectPicker {
                    id: picker
                    hoverEnabled: false
                    onPressed: {
                        if(Qt.LeftButton & pick.buttons)
                        {
                            if(!doubleClickTimer.running)
                                doubleClickTimer.start()
                            else
                                mainCamera.viewCenter = pick.worldIntersection
                        }
                    }

                    Timer {
                        id: doubleClickTimer
                        running: false
                        interval: 400
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
                            unmirrorTextures(parent);
                        }
                    }
                }
                Locator3D { enabled: locatorCheckBox.checked}
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
        }
    }

    // menus
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
