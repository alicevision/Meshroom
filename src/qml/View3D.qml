import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3
import QtQuick.Scene3D 2.0
import Qt3D.Core 2.0
import Qt3D.Render 2.0
import Qt3D.Input 2.0
import Qt3D.Extras 2.0
import Qt3D.Logic 2.0
import AlembicEntity 1.0
import MayaCameraController 1.0
import "controls"

Frame {

    id: root

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

    function loadModel(url)
    {
        abcEntity.url = modelLoader.source = "";
        if(!url.trim())
            return;
        if(url.split(".").pop() == "abc")
            abcEntity.url = Qt.resolvedUrl(url)
        else
            modelLoader.source = Qt.resolvedUrl(url)
    }

    // connections
    Connections {
        target: _window
        onDisplayIn3DView: {
            sourceName.text = ""
            sourceListView.model = 0;
            var source = "";
            if(attribute && attribute.value)
            {
                sourceName.text = attribute.name
                sourceListView.model = Array.isArray(attribute.value) ? attribute.value : [attribute.value]
                source = sourceListView.model[0];
            }
            loadModel(source);
        }
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
                onMousePressed: scene3D.forceActiveFocus()
                onMouseReleased: {
                    if(moving)
                        return;
                    switch(mouse.button) {
                        case Qt.LeftButton:
                            panel.close()
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

                    activeFrameGraph: Viewport {
                        normalizedRect: Qt.rect(0.0, 0.0, 1.0, 1.0)
                        RenderSurfaceSelector {
                            CameraSelector {
                                id: cameraSelector
                                camera: mainCamera
                                FrustumCulling {
                                    ClearBuffers {
                                        buffers : ClearBuffers.ColorDepthBuffer
                                        clearColor: Qt.rgba(0, 0, 0, 0.2)
                                    }
                                }
                            }
                        }
                    }
                },
                InputSettings {
                    eventSource: _window
                    enabled: true
                }
            ]

            AlembicEntity {
                id: abcEntity
                particleSize: 0.1
                onObjectPicked: {
                    // if(cameraController.moving)
                    //     return;
                    // mainCamera.position = transform.translation;
                    // mainCamera.upVector = Qt.vector3d(0.0, 1.0, 0.0);
                    // mainCamera.viewCenter = transform.translation.plus(Qt.vector3d(0, 0, -1));
                    // mainCamera.roll(transform.rotationZ);
                    // mainCamera.pan(transform.rotationY);
                    // mainCamera.tilt(transform.rotationX);
                }
            }
            Entity {
                id: modelLoader
                property alias source: scene.source
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
                    onStatusChanged: {
                        if(scene.status == SceneLoader.Ready)
                            unmirrorTextures(parent);
                    }
                }
            }

            // Grid
            Entity {
                id: gridEntity
                components: [
                    GeometryRenderer {
                        primitiveType: GeometryRenderer.Lines
                        geometry: Geometry {
                            Attribute {
                                id: gridPosition
                                attributeType: Attribute.VertexAttribute
                                vertexBaseType: Attribute.Float
                                vertexSize: 3
                                count: 0
                                name: defaultPositionAttributeName
                                buffer: Buffer {
                                    type: Buffer.VertexBuffer
                                    data: {
                                        function buildGrid(first, last, offset, attribute) {
                                            var vertexCount = (((last-first)/offset)+1)*4;
                                            var f32 = new Float32Array(vertexCount*3);
                                            for(var id = 0, i = first; i <= last; i += offset, id++)
                                            {
                                                f32[12*id] = i;
                                                f32[12*id+1] = 0.0;
                                                f32[12*id+2] = first;

                                                f32[12*id+3] = i;
                                                f32[12*id+4] = 0.0;
                                                f32[12*id+5] = last;

                                                f32[12*id+6] = first;
                                                f32[12*id+7] = 0.0;
                                                f32[12*id+8] = i;

                                                f32[12*id+9] = last;
                                                f32[12*id+10] = 0.0;
                                                f32[12*id+11] = i;
                                            }
                                            attribute.count = vertexCount;
                                            return f32;
                                        }
                                        return buildGrid(-12, 12, 1, gridPosition);
                                    }
                                }
                            }
                            boundingVolumePositionAttribute: gridPosition
                        }
                    },
                    PhongMaterial {
                        ambient: Qt.rgba(0.4, 0.4, 0.4, 1)
                    }
                ]
            }

            // Gizmo
            Entity {
                id: gizmoEntity
                components: [
                    GeometryRenderer {
                        primitiveType: GeometryRenderer.Lines
                        geometry: Geometry {
                            Attribute {
                                id: gizmoPosition
                                attributeType: Attribute.VertexAttribute
                                vertexBaseType: Attribute.Float
                                vertexSize: 3
                                count: 6
                                name: defaultPositionAttributeName
                                buffer: Buffer {
                                    type: Buffer.VertexBuffer
                                    data: Float32Array([
                                        0.0, 0.001, 0.0,
                                        1.0, 0.001, 0.0,
                                        0.0, 0.001, 0.0,
                                        0.0, 1.001, 0.0,
                                        0.0, 0.001, 0.0,
                                        0.0, 0.001, 1.0
                                        ])
                                }
                            }
                            Attribute {
                                attributeType: Attribute.VertexAttribute
                                vertexBaseType: Attribute.Float
                                vertexSize: 3
                                count: 6
                                name: defaultColorAttributeName
                                buffer: Buffer {
                                    type: Buffer.VertexBuffer
                                    data: Float32Array([
                                        1.0, 0.0, 0.0,
                                        1.0, 0.0, 0.0,
                                        0.0, 1.0, 0.0,
                                        0.0, 1.0, 0.0,
                                        0.0, 0.0, 1.0,
                                        0.0, 0.0, 1.0
                                        ])
                                }
                            }
                            boundingVolumePositionAttribute: gizmoPosition
                        }
                    },
                    PerVertexColorMaterial {},
                    Transform { id: gizmoTransform }
                ]
            }
        }
    }

    // menus
    Menu {
        id: contextMenu
        MenuItem {
            text: "Reset camera position [F]"
            onTriggered: {
                resetCameraCenter();
                resetCameraPosition();
            }
        }
    }

    // overlay panel
    SidePanel {
        id: panel
        anchors.fill: parent
        icons: [ "qrc:///images/gear.svg", "qrc:///images/output.svg"]
        Flickable {
            anchors.fill: parent
            ScrollBar.vertical: ScrollBar {}
            contentWidth: parent.width
            contentHeight: 300
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10
                Label {
                    Layout.fillWidth: true
                    text: "VIEW SETTINGS"
                    state: "small"
                }
                GridLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    columns: 2
                    Label {
                        Layout.fillWidth: true
                        text: "show grid"
                        state: "xsmall"
                    }
                    CheckBox {
                        Layout.fillWidth: true
                        text: "grid"
                        checked: true
                        onClicked: gridEntity.parent = checked ? rootEntity : null
                        focusPolicy: Qt.NoFocus
                    }
                    Label {
                        Layout.fillWidth: true
                        text: "show axis"
                        state: "xsmall"
                    }
                    CheckBox {
                        Layout.fillWidth: true
                        text: "axis"
                        checked: true
                        onClicked: gizmoEntity.parent = checked ? rootEntity : null
                        focusPolicy: Qt.NoFocus
                    }
                    Label {
                        Layout.fillWidth: true
                        text: "point size"
                        state: "xsmall"
                    }
                    Slider {
                        Layout.fillWidth: true
                        from: 0.1
                        to: 20
                        stepSize: 0.01
                        value: 0.5
                        onPositionChanged: abcEntity.particleSize = (from + (to-from) * visualPosition)*0.01
                        focusPolicy: Qt.NoFocus
                    }
                    Label {
                        Layout.fillWidth: true
                        text: "locator scale"
                        state: "xsmall"
                    }
                    Slider {
                        Layout.fillWidth: true
                        from: 0.01
                        to: 10
                        stepSize: 0.01
                        value: 1
                        onPositionChanged: {
                            var value = (from + (to-from) * visualPosition);
                            abcEntity.locatorScale = value;
                            gizmoTransform.scale = value;
                        }
                        focusPolicy: Qt.NoFocus
                    }
                    Item { Layout.fillHeight: true } // spacer
                }
            }
        }
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 10
            RowLayout {
                Label {
                    Layout.fillWidth: true
                    text: "VIEW INPUTS"
                    state: "small"
                }
                Label {
                    id: sourceName
                    horizontalAlignment: Text.AlignRight
                    enabled: false
                    state: "small"
                    text: ""
                }
            }
            ListView {
                id: sourceListView
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 1
                delegate: Button {
                    width: ListView.view.width
                    height: 30
                    text: modelData
                    onClicked: loadModel(Qt.resolvedUrl(modelData))
                }
            }
        }
    }
}
