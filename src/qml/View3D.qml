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
        						name: defaultPositionAttributeName()
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
        						name: defaultPositionAttributeName()
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
        						name: defaultColorAttributeName()
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
                    PerVertexColorMaterial {}
                ]
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
