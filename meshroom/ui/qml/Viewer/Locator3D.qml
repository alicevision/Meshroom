import QtQuick 2.7
import Qt3D.Core 2.0
import Qt3D.Render 2.0
import Qt3D.Extras 2.0

// Locator
Entity {
    id: locatorEntity
    components: [
        GeometryRenderer {
            primitiveType: GeometryRenderer.Lines
            geometry: Geometry {
                Attribute {
                    id: locatorPosition
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
                boundingVolumePositionAttribute: locatorPosition
            }
        },
        PerVertexColorMaterial {},
        Transform { id: locatorTransform }
    ]
}
