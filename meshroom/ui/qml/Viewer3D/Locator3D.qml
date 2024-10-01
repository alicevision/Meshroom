import QtQuick
import Qt3D.Core 2.6
import Qt3D.Render 2.6
import Qt3D.Extras 2.15

import Utils 1.0

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
                        data: new Float32Array([
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
                        data: new Float32Array([
                            Colors.red.r, Colors.red.g, Colors.red.b,
                            Colors.red.r, Colors.red.g, Colors.red.b,
                            Colors.green.r, Colors.green.g, Colors.green.b,
                            Colors.green.r, Colors.green.g, Colors.green.b,
                            Colors.blue.r, Colors.blue.g, Colors.blue.b,
                            Colors.blue.r, Colors.blue.g, Colors.blue.b
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
