import QtQuick
import Qt3D.Core 2.6
import Qt3D.Render 2.6
import Qt3D.Extras 2.15

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
                        data: {
                            function buildGrid(first, last, offset, attribute) {
                                var vertexCount = (((last - first) / offset) + 1) * 4
                                var f32 = new Float32Array(vertexCount * 3)
                                for (var id = 0, i = first; i <= last; i += offset, id++) {
                                    f32[12 * id] = i
                                    f32[12 * id + 1] = 0.0
                                    f32[12 * id + 2] = first

                                    f32[12 * id + 3] = i
                                    f32[12 * id + 4] = 0.0
                                    f32[12 * id + 5] = last

                                    f32[12 * id + 6] = first
                                    f32[12 * id + 7] = 0.0
                                    f32[12 * id + 8] = i

                                    f32[12 * id + 9] = last
                                    f32[12 * id + 10] = 0.0
                                    f32[12 * id + 11] = i
                                }
                                attribute.count = vertexCount
                                return f32
                            }
                            return buildGrid(-12, 12, 1, gridPosition)
                        }
                    }
                }
                boundingVolumePositionAttribute: gridPosition
            }
        },
        PhongMaterial {
            ambient: "#FFF"
            diffuse: "#222"
            specular: diffuse
            shininess: 0
        }
    ]
}
