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
                Attribute {
                    id: gridNormal
                    attributeType: Attribute.VertexAttribute
                    vertexBaseType: Attribute.Float
                    vertexSize: 3
                    count: gridPosition.count
                    name: defaultNormalAttributeName
                    buffer: Buffer {
                        data: {
                            var f32 = new Float32Array(gridPosition.count * 3)
                            for (var i = 0; i < gridPosition.count; i++) {
                                f32[3 * i] = 0.0
                                f32[3 * i + 1] = 1.0
                                f32[3 * i + 2] = 0.0
                            }
                            return f32
                        }
                    }
                }
                boundingVolumePositionAttribute: gridPosition
            }
        },
        // Neutralized Phong: diffuse/specular zeroed so the equation collapses
        // to just `ambient`, giving an unlit-looking constant color. This way
        // the (0,1,0) placeholder normals in the geometry above never affect
        // the final shading, while we stay on the PhongMaterial code path that
        // Metal RHI vertex-descriptor validation is happy with.
        PhongMaterial {
            ambient: "#FFF"
            diffuse: "#000"
            specular: "#000"
            shininess: 0
        }
    ]
}
