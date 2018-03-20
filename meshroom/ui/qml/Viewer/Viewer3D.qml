import QtQuick 2.7
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import QtQuick.Scene3D 2.0
import Qt3D.Core 2.1
import Qt3D.Render 2.1
import Qt3D.Input 2.1 as Qt3DInput // to avoid clash with Controls2 Action

import MaterialIcons 2.2

import Controls 1.0

FocusScope {
    id: root

    property alias source: modelLoader.source
    property alias abcSource: modelLoader.abcSource
    property alias depthMapSource: modelLoader.depthMapSource

    property int renderMode: 2
    readonly property alias loading: modelLoader.loading
    readonly property alias polyCount: modelLoader.polyCount

    // Alembic optional support => won't be available if AlembicEntity plugin is not available
    readonly property Component abcLoaderComp: Qt.createComponent("AlembicLoader.qml")
    readonly property bool supportAlembic: abcLoaderComp.status == Component.Ready
    readonly property Component depthMapLoaderComp: Qt.createComponent("DepthMapLoader.qml")
    readonly property bool supportDepthMap: depthMapLoaderComp.status == Component.Ready

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
            var mats = []
            var hasTextures = false
            // Create as many MaterialSwitcher as individual materials for this entity
            // NOTE: we let each MaterialSwitcher modify the components of the entity
            //       and therefore remove the default material spawned by the sceneLoader
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
                        "mode": root.renderMode
                    }
                    mats.push(m)
                    hasTextures = true
                }

                if(comp.toString().indexOf("QPhongMaterial") > -1) {
                    // create MaterialSwitcher with default colors
                    mats.push({})
                }
                // Retrieve polycount using vertexPosition buffer
                if(comp.toString().indexOf("Geometry") > -1) {
                    for(var k = 0; k < comp.geometry.attributes.length; ++k)
                    {
                        if(comp.geometry.attributes[k].name == "vertexPosition")
                            modelLoader.polyCount += comp.geometry.attributes[k].count / 3
                    }
                }
            }

            modelLoader.meshHasTexture = mats.length > 0
            mats.forEach(function(m){
                // create a material switcher for each material definition
                var matSwitcher = materialSwitcherComponent.createObject(entity, m)
                matSwitcher.mode = Qt.binding(function(){ return root.renderMode })
            })
        })
    }

    Component {
        id: materialSwitcherComponent
        MaterialSwitcher {}
    }

    function clear()
    {
        clearScene()
        clearAbc()
    }

    function clearScene()
    {
        source = 'no_file' // only way to force unloading of valid scene
        source = ''
        modelLoader.polyCount = 0
    }

    function clearAbc()
    {
        abcSource = ''
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
                nearPlane : 0.01
                farPlane : 1000.0
                position: Qt.vector3d(28.0, 21.0, 28.0)
                upVector: Qt.vector3d(0.0, 1.0, 0.0)
                viewCenter: Qt.vector3d(0.0, 0.0, 0.0)
                aspectRatio: width/height

                Behavior on viewCenter {
                    Vector3dAnimation { duration: 250 }
                }
            }

            // Scene light, attached to the camera
            Entity {
                components: [
                    PointLight {
                        color: "white"
                    },
                    Transform {
                        translation: mainCamera.position
                    }
                ]
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
                property string abcSource
                property string depthMapSource
                property int polyCount
                property bool meshHasTexture: false
                // SceneLoader status is not reliable when loading a 3D file
                property bool loading: false
                onSourceChanged: {
                    meshHasTexture = false
                    loading = true
                }
                onAbcSourceChanged: {
                    if(root.supportAlembic)
                        loading = true
                }

                components: [sceneLoaderEntity, transform, picker]

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

                Entity {
                    id: sceneLoaderEntity
                    enabled: showMeshCheckBox.checked

                    components: [
                        SceneLoader {
                            id: scene
                            source: modelLoader.source
                            onStatusChanged: {
                                if(scene.status != SceneLoader.Loading)
                                    modelLoader.loading = false;
                                if(scene.status == SceneLoader.Ready)
                                {
                                    setupMaterialSwitchers(modelLoader)
                                }
                            }
                        }
                    ]
                }

                Entity {
                    id: abcLoaderEntity
                    // Instantiate the AlembicEntity dynamically
                    // to avoid import errors if the plugin is not available
                    property Entity abcLoader: null
                    enabled: showSfMCheckBox.checked

                    Component.onCompleted: {
                        if(!root.supportAlembic) // Alembic plugin not available
                            return

                        // destroy previously created entity
                        if(abcLoader != undefined)
                            abcLoader.destroy()

                        abcLoader = abcLoaderComp.createObject(abcLoaderEntity, {
                                                       'url': Qt.binding(function() { return modelLoader.abcSource } ),
                                                       'particleSize': Qt.binding(function() { return 0.01 * transform.scale }),
                                                       'locatorScale': Qt.binding(function() { return 0.2})
                                                   });
                        // urlChanged signal is emitted once the Alembic file is loaded
                        // set the 'loading' property to false when it's emitted
                        // TODO: AlembicEntity should expose a status
                        abcLoader.onUrlChanged.connect(function(){ modelLoader.loading = false })
                        modelLoader.loading = false
                    }
                }

                Entity {
                    id: depthMapLoaderEntity
                    // Instantiate the DepthMapEntity dynamically
                    // to avoid import errors if the plugin is not available
                    property Entity depthMapLoader: null
                    enabled: showDepthMapCheckBox.checked

                    Component.onCompleted: {
                        if(!root.supportDepthMap) // DepthMap plugin not available
                            return

                        // destroy previously created entity
                        if(depthMapLoader != undefined)
                            depthMapLoader.destroy()

                        depthMapLoader = depthMapLoaderComp.createObject(depthMapLoaderEntity, {
                                                       'source': Qt.binding(function() { return modelLoader.depthMapSource } )
                                                   });
                        // 'sourceChanged' signal is emitted once the depthMap file is loaded
                        // set the 'loading' property to false when it's emitted
                        // TODO: DepthMapEntity should expose a status
                        depthMapLoader.onSourceChanged.connect(function(){ modelLoader.loading = false })
                        modelLoader.loading = false
                    }
                }

                Locator3D { enabled: locatorCheckBox.checked }
            }
            Grid3D { enabled: gridCheckBox.checked }
        }
    }

    //
    //  UI Overlay
    //

    // Rotation/Scale
    FloatingPane {
        anchors { top: parent.top; left: parent.left }

        GridLayout {
            id: controlsLayout
            columns: 2
            columnSpacing: 12
            property int sliderWidth: 100

            // Rotation Controls
            Label {
                font.family: MaterialIcons.fontFamily
                text: MaterialIcons.rotation3D
                font.pointSize: 14
                Layout.rowSpan: 3
            }

            Row {
                spacing: 4
                Slider { width: controlsLayout.sliderWidth; from: -180; to: 180; onPositionChanged: transform.rotationX = value }
                Label { text: "X" }
            }

            Row {
                spacing: 4
                Slider { width: controlsLayout.sliderWidth; from: -180; to: 180; onPositionChanged: transform.rotationY = value }
                Label { text: "Y" }
            }

            Row {
                spacing: 4
                Slider { width: controlsLayout.sliderWidth; from: -180; to: 180; onPositionChanged: transform.rotationZ = value }
                Label { text: "Z" }
            }

            // Scale Control
            Label { text: "Scale" }
            Slider { implicitWidth: controlsLayout.sliderWidth; from: 1; to: 10; onPositionChanged: transform.scale = value }
        }
    }

    // Outliner
    FloatingPane {
        anchors { top: parent.top; right: parent.right }

        Column {
            Row {
                CheckBox { id: showSfMCheckBox; text: "SfM"; checked: true; visible: root.supportAlembic; opacity: root.abcSource ? 1.0 : 0.6 }
                ToolButton {
                    text: MaterialIcons.clear; font.family: MaterialIcons.fontFamily; visible: root.abcSource != '';
                    onClicked: clearAbc()
                    ToolTip.text: "Unload"
                    ToolTip.visible: hovered
                }
            }
            Row {
                visible: root.depthMapSource != ''
                CheckBox { id: showDepthMapCheckBox; text: "DepthMap"; checked: true; }
                ToolButton {
                    text: MaterialIcons.clear; font.family: MaterialIcons.fontFamily;
                    onClicked: root.depthMapSource = ''
                    ToolTip.text: "Unload"
                    ToolTip.visible: hovered
                }
            }
            Row {
                CheckBox { id: showMeshCheckBox; text: "Mesh"; checked: true; opacity: root.source ? 1.0 : 0.6 }
                ToolButton {
                    text: MaterialIcons.clear; font.family: MaterialIcons.fontFamily; visible: root.source != '';
                    onClicked: clearScene()
                    ToolTip.text: "Unload"
                    ToolTip.visible: hovered
                }
            }
            CheckBox { id: gridCheckBox; text: "Grid"; checked: true }
            CheckBox { id: locatorCheckBox; text: "Locator"; checked: true }
        }
    }

    // Render Mode
    FloatingPane {
        anchors { bottom: parent.bottom; left: parent.left }


        Row {
            anchors.verticalCenter: parent.verticalCenter
            Repeater {
                model: [ // Can't use ListModel because of MaterialIcons expressions
                    {"name": "Solid", "icon": MaterialIcons.crop_din},
                    {"name": "Wireframe", "icon": MaterialIcons.grid_on},
                    {"name": "Textured", "icon": MaterialIcons.texture },
                ]
                delegate: ToolButton {
                    text: modelData["icon"]
                    ToolTip.text: modelData["name"]
                    ToolTip.visible: hovered
                    font.family: MaterialIcons.fontFamily
                    font.pointSize: 11
                    padding: 4
                    onClicked: root.renderMode = index
                    checkable: !checked // hack to disable check toggle on click
                    checked: renderMode === index
                }
            }
        }
    }

    FloatingPane {
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        visible: modelLoader.polyCount > 0
        Label {
            text: modelLoader.polyCount + " faces"
        }
    }

    // Menu
    Menu {
        id: contextMenu

        MenuItem {
            text: "Fit All"
            onTriggered: mainCamera.viewAll()
        }
        MenuItem {
            text: "Reset View"
            onTriggered: resetCameraPosition()
        }
    }
}
