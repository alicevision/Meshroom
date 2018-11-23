import QtQuick 2.7
import QtQuick.Controls 2.3
import QtQuick.Controls 1.4 as Controls1
import QtQuick.Layouts 1.3
import QtQml.Models 2.2
import QtQuick.Scene3D 2.0
import Qt3D.Core 2.1
import Qt3D.Render 2.1
import Qt3D.Extras 2.1
import Qt3D.Input 2.1 as Qt3DInput // to avoid clash with Controls2 Action

import MaterialIcons 2.2

import Controls 1.0


FocusScope {
    id: root

    property int renderMode: 2
    property alias library: mediaLibrary
    property alias inspector: inspector3d

    readonly property vector3d defaultCamPosition: Qt.vector3d(12.0, 10.0, -12.0)
    readonly property vector3d defaultCamUpVector: Qt.vector3d(0.0, 1.0, 0.0)
    readonly property vector3d defaultCamViewCenter: Qt.vector3d(0.0, 0.0, 0.0)

    // functions
    function resetCameraPosition() {
        mainCamera.position = defaultCamPosition;
        mainCamera.upVector = defaultCamUpVector;
        mainCamera.viewCenter = defaultCamViewCenter;
    }

    function load(filepath) {
        mediaLibrary.load(filepath);
    }

    function view(attribute) {
        mediaLibrary.view(attribute)
    }

    function clear() {
        mediaLibrary.clear()
    }

    SystemPalette { id: activePalette }


    Scene3D {
        id: scene3D
        anchors.fill: parent
        cameraAspectRatioMode: Scene3D.AutomaticAspectRatio // vs. UserAspectRatio
        hoverEnabled: true // if true, will trigger positionChanged events in attached MouseHandler
        aspects: ["logic", "input"]
        focus: true


        Keys.onPressed: {
            if (event.key == Qt.Key_F) {
                resetCameraPosition();
            }
            else if(Qt.Key_1 <= event.key && event.key <= Qt.Key_3)
            {
                Viewer3DSettings.renderMode = event.key - Qt.Key_1;
            }
            else {
                event.accepted = false
            }
        }

        Entity {
            id: rootEntity

            Camera {
                id: mainCamera
                projectionType: CameraLens.PerspectiveProjection
                fieldOfView: 45
                nearPlane : 0.01
                farPlane : 10000.0
                position: defaultCamPosition
                upVector: defaultCamUpVector
                viewCenter: defaultCamViewCenter
                aspectRatio: width/height

                Behavior on viewCenter {
                    Vector3dAnimation { duration: 250 }
                }
                Behavior on position {
                    Vector3dAnimation { duration: 250 }
                }

                // Scene light, attached to the camera
                Entity {
                    components: [
                        PointLight {
                            color: "white"
                        }
                    ]
                }
            }

            Entity {
                components: [
                    SphereMesh {
                    },
                    Transform {
                        id: viewCenterTransform
                        translation: mainCamera.viewCenter
                        scale: 0.005 * mainCamera.viewCenter.minus(mainCamera.position).length()
                    },
                    PhongMaterial {
                        ambient: "#FFF"
                        shininess: 0.2
                        diffuse: activePalette.highlight
                        specular: activePalette.highlight
                    }
                ]
            }

            DefaultCameraController {
                id: cameraController
                camera: mainCamera
                focus: scene3D.activeFocus
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
                    pickingSettings.pickMethod: PickingSettings.PrimitivePicking  // enables point/edge/triangle picking
                    pickingSettings.pickResultMode: PickingSettings.NearestPick
                    renderPolicy: RenderSettings.OnDemand

                    activeFrameGraph: RenderSurfaceSelector {
                        // Use the whole viewport
                        Viewport {
                            normalizedRect: Qt.rect(0.0, 0.0, 1.0, 1.0)
                            CameraSelector {
                                id: cameraSelector
                                camera: mainCamera
                                FrustumCulling {
                                    ClearBuffers {
                                        clearColor: "transparent"
                                        buffers : ClearBuffers.ColorDepthBuffer
                                        RenderStateSet {
                                            renderStates: [
                                                PointSize {
                                                    sizeMode: Viewer3DSettings.fixedPointSize ? PointSize.Fixed : PointSize.Programmable
                                                    value: Viewer3DSettings.pointSize
                                                },
                                                DepthTest { depthFunction: DepthTest.Less }
                                            ]
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                Qt3DInput.InputSettings { }
            ]

            MediaLibrary {
                id: mediaLibrary
                renderMode: Viewer3DSettings.renderMode
                // Picking to set focus point (camera view center)
                // Only activate it when a double click may happen or when the 'Control' key is pressed
                pickingEnabled: cameraController.pickingActive || doubleClickTimer.running

                components: [
                    Transform {
                        id: transform
                    }
                ]

                onPressed: {
                    if(pick.button == Qt.LeftButton)
                    {
                        mainCamera.viewCenter = pick.worldIntersection;
                    }
                    doubleClickTimer.stop();
                }

                Locator3D { enabled: Viewer3DSettings.displayLocator }
            }

            Grid3D { enabled: Viewer3DSettings.displayGrid }
        }
    }

    //  UI Overlay
    Controls1.SplitView {
        id: overlaySplitView
        anchors.fill: parent

        Item { Layout.fillWidth: true; Layout.minimumWidth: parent.width * 0.5  }

        Inspector3D {
            id: inspector3d
            width: 200
            Layout.minimumWidth: 5

            camera: mainCamera
            targetTransform: transform
            mediaLibrary: mediaLibrary
        }
    }

    // Rendering modes
    FloatingPane {
        anchors.bottom: parent.bottom
        padding: 4
        Row {
            Repeater {
                model: Viewer3DSettings.renderModes

                delegate: MaterialToolButton {
                    text: modelData["icon"]
                    ToolTip.text: modelData["name"] + " (" + (index+1) + ")"
                    font.pointSize: 11
                    onClicked: Viewer3DSettings.renderMode = index
                    checked: Viewer3DSettings.renderMode === index
                    checkable: !checked // hack to disabled check on toggle
                }
            }
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
