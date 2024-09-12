import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Scene3D 2.6
import Qt3D.Core 2.6
import Qt3D.Render 2.6
import Qt3D.Extras 2.15
import Qt3D.Input 2.6 as Qt3DInput // to avoid clash with Controls2 Action

import Controls 1.0
import MaterialIcons 2.2
import Utils 1.0


FocusScope {
    id: root

    property int renderMode: 2
    readonly property alias library: mediaLibrary
    readonly property alias mainCamera: mainCamera

    readonly property vector3d defaultCamPosition: Qt.vector3d(12.0, 10.0, -12.0)
    readonly property vector3d defaultCamUpVector: Qt.vector3d(-0.358979, 0.861550, 0.358979) // should be accurate, consistent with camera view center
    readonly property vector3d defaultCamViewCenter: Qt.vector3d(0.0, 0.0, 0.0)

    readonly property var viewpoint: _reconstruction ? _reconstruction.selectedViewpoint : null
    readonly property bool doSyncViewpointCamera: Viewer3DSettings.syncViewpointCamera && (viewpoint && viewpoint.isReconstructed)

    // Functions
    function resetCameraPosition() {
        mainCamera.position = defaultCamPosition
        mainCamera.upVector = defaultCamUpVector
        mainCamera.viewCenter = defaultCamViewCenter
    }

    function load(filepath, label = undefined) {
        mediaLibrary.load(filepath, label)
    }

    /// View 'attribute' in the 3D Viewer. Media will be loaded if needed.
    /// Returns whether the attribute can be visualized (matching type and extension).
    function view(attribute) {
        if (attribute.desc.type === "File"
           && Viewer3DSettings.supportedExtensions.indexOf(Filepath.extension(attribute.value)) > - 1) {
            mediaLibrary.view(attribute)
            return true
        }
        return false
    }

    /// Solo (i.e display only) the given attribute.
    function solo(attribute) {
        mediaLibrary.solo(mediaLibrary.find(attribute))
    }

    function clear() {
        mediaLibrary.clear()
    }

    SystemPalette { id: activePalette }

    Scene3D {
        id: scene3D
        anchors.fill: parent
        cameraAspectRatioMode: Scene3D.AutomaticAspectRatio  // vs. UserAspectRatio
        hoverEnabled: true  // If true, will trigger positionChanged events in attached MouseHandler
        aspects: ["logic", "input"]
        focus: true

        // We cannot use directly an ExifOrientedViewer since this component is not a Loader
        // so we redefine the transform using the ExifOrientation utility functions
        property var orientationTag: (doSyncViewpointCamera && root.viewpoint) ? root.viewpoint.orientation.toString() : "1"
        transform: [
            Rotation {
                angle: ExifOrientation.rotation(scene3D.orientationTag)
                origin.x: scene3D.width * 0.5
                origin.y: scene3D.height * 0.5
            },
            Scale {
                xScale: ExifOrientation.xscale(scene3D.orientationTag)
                origin.x: scene3D.width * 0.5
                origin.y: scene3D.height * 0.5
            }
        ]

        Keys.onPressed: function(event) {
            if (event.key === Qt.Key_F) {
                resetCameraPosition()
            } else if (Qt.Key_1 <= event.key && event.key < Qt.Key_1 + Viewer3DSettings.renderModes.length) {
                Viewer3DSettings.renderMode = event.key - Qt.Key_1
            } else {
                event.accepted = false
            }
        }

        Entity {
            id: rootEntity

            Camera {
                id: mainCamera
                projectionType: CameraLens.PerspectiveProjection
                enabled: cameraSelector.camera == mainCamera
                fieldOfView: 45
                nearPlane : 0.01
                farPlane : 10000.0
                position: defaultCamPosition
                upVector: defaultCamUpVector
                viewCenter: defaultCamViewCenter
                aspectRatio: width/height
            }

            ViewpointCamera {
                id: viewpointCamera
                enabled: cameraSelector.camera === camera
                viewpoint: root.viewpoint
                camera.aspectRatio: width/height
            }

            Entity {
                components: [
                    DirectionalLight{
                        color: "white"
                        worldDirection: Transformations3DHelper.getRotatedCameraViewVector(cameraSelector.camera.viewVector, cameraSelector.camera.upVector, directionalLightPane.lightPitchValue, directionalLightPane.lightYawValue).normalized()
                    }
                ]
            }

            TrackballGizmo {
                beamRadius: 4.0/root.height
                alpha: cameraController.moving ? 1.0 : 0.7
                enabled: Viewer3DSettings.displayGizmo && cameraSelector.camera == mainCamera
                xColor: Colors.red
                yColor: Colors.green
                zColor: Colors.blue
                centerColor: Colors.sysPalette.highlight
                transform: Transform {
                    translation: mainCamera.viewCenter
                    scale: 0.15 * mainCamera.viewCenter.minus(mainCamera.position).length()
                }
            }

            DefaultCameraController {
                id: cameraController
                enabled: cameraSelector.camera == mainCamera

                windowSize {
                    width: root.width
                    height: root.height
                }
                rotationSpeed: 16
                trackballSize: 0.9

                camera: mainCamera
                focus: scene3D.activeFocus
                onMousePressed: function(mouse) {
                    scene3D.forceActiveFocus()
                }
                onMouseReleased: function(mouse, moved) {
                    if (moving)
                        return
                    if (!moved && mouse.button === Qt.RightButton) {
                        contextMenu.popup()
                    }
                }
            }

            components: [
                RenderSettings {
                    pickingSettings.pickMethod: PickingSettings.PrimitivePicking  // Enables point/edge/triangle picking
                    pickingSettings.pickResultMode: PickingSettings.NearestPick
                    renderPolicy: RenderSettings.Always

                    activeFrameGraph: RenderSurfaceSelector {
                        // Use the whole viewport
                        Viewport {
                            normalizedRect: Qt.rect(0.0, 0.0, 1.0, 1.0)
                            CameraSelector {
                                id: cameraSelector
                                camera: doSyncViewpointCamera ? viewpointCamera.camera : mainCamera
                                FrustumCulling {
                                    ClearBuffers {
                                        clearColor: "transparent"
                                        buffers : ClearBuffers.ColorDepthBuffer
                                        RenderStateSet {
                                            renderStates: [
                                                DepthTest { depthFunction: DepthTest.Less }
                                            ]
                                        }
                                    }
                                    LayerFilter {
                                        filterMode: LayerFilter.DiscardAnyMatchingLayers
                                        layers: Layer {id: drawOnFront}
                                    }
                                    LayerFilter {
                                        filterMode: LayerFilter.AcceptAnyMatchingLayers
                                        layers: [drawOnFront]
                                        RenderStateSet {
                                            renderStates: DepthTest { depthFunction: DepthTest.GreaterOrEqual }
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
                // Only activate it when the 'Control' key is pressed
                pickingEnabled: cameraController.pickingActive
                camera: cameraSelector.camera

                // Used for TransformGizmo in BoundingBox
                sceneCameraController: cameraController
                frontLayerComponent: drawOnFront
                window: root

                components: [
                    Transform {
                        id: transform
                    }
                ]

                onClicked: function(pick) {
                    if (pick.button === Qt.LeftButton) {
                        mainCamera.viewCenter = pick.worldIntersection
                    }
                }

            }
            Locator3D { enabled: Viewer3DSettings.displayOrigin }
            Grid3D { enabled: Viewer3DSettings.displayGrid }
        }
    }

    // Image overlay when navigating reconstructed cameras
    Loader {
        id: imageOverlayLoader
        anchors.fill: parent

        active: doSyncViewpointCamera
        visible: Viewer3DSettings.showViewpointImageOverlay

        sourceComponent: ImageOverlay {
            id: imageOverlay
            source: root.viewpoint.undistortedImageSource
            imageRatio: root.viewpoint.orientedImageSize.width * root.viewpoint.pixelAspectRatio / root.viewpoint.orientedImageSize.height
            uvCenterOffset: root.viewpoint.uvCenterOffset
            showFrame: Viewer3DSettings.showViewpointImageFrame
            imageOpacity: Viewer3DSettings.viewpointImageOverlayOpacity
        }
    }

    // Media loading overlay
    // (Scene3D is frozen while a media is being loaded)
    Rectangle {
        anchors.fill: parent
        visible: mediaLibrary.loading
        color: Qt.darker(Colors.sysPalette.mid, 1.2)
        opacity: 0.6
        BusyIndicator {
            anchors.centerIn: parent
            running: parent.visible
        }
    }

    FloatingPane {
        visible: Viewer3DSettings.renderMode == 3
        anchors.bottom: renderModesPanel.top
        GridLayout {
            columns: 2
            rowSpacing: 0

            RadioButton {
                text: "SHL File"
                autoExclusive: true
                checked: true
            }
            TextField {
                text: Viewer3DSettings.shlFile
                selectByMouse: true
                Layout.minimumWidth: 300
                onEditingFinished: Viewer3DSettings.shlFile = text
            }

            RadioButton {
                Layout.columnSpan: 2
                autoExclusive: true
                text: "Normals"
                onCheckedChanged: Viewer3DSettings.displayNormals = checked
            }

        }
    }

    // Rendering modes
    FloatingPane {
        id: renderModesPanel
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
                    checkable: !checked  // Hack to disabled check on toggle
                }
            }
        }
    }

    // Directional light controller
    DirectionalLightPane {
        id: directionalLightPane
        anchors {
            bottom: parent.bottom
            right: parent.right
            margins: 2
        }
        visible: Viewer3DSettings.displayLightController
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
