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

Item {

    Connections {
        target: _window
        onLoadAlembic: abcEntity.url = Qt.resolvedUrl(file)
    }

    DropArea {
        anchors.fill: parent
        onDropped: abcEntity.url = drop.urls[0]
    }

    Scene3D {
        anchors.fill: parent
        focus: true
        cameraAspectRatioMode: Scene3D.AutomaticAspectRatio // vs. UserAspectRatio
        aspects: ["logic", "input"]
        Entity {
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
            }
            MayaCameraController { camera: mainCamera }
            components: [
                RenderSettings {
                    activeFrameGraph: Viewport {
                        normalizedRect: Qt.rect(0.0, 0.0, 1.0, 1.0)
                        RenderSurfaceSelector {
                            CameraSelector {
                                id: cameraSelector
                                camera: mainCamera
                                FrustumCulling {
                                    ClearBuffers {
                                        buffers : ClearBuffers.ColorDepthBuffer
                                        clearColor: Qt.rgba(0.2, 0.2, 0.2, 1)
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
            }
        }
    }

    Slider {
        focusPolicy: Qt.NoFocus
        from: 0.1
        to: 2
        stepSize: 0.01
        value: 0.5
        onPositionChanged: abcEntity.particleSize = (from + (to-from) * visualPosition)*0.01
    }

}
