import QtQuick
import Qt3D.Core 2.6
import Qt3D.Render 2.6
import Qt3D.Extras 2.15

import Utils 1.0

// Grid
Entity {
    id: gridEntity

    property int first: -12
    property int last: 12
    property int offset: 1

    // Set of line segments drawn with a constant color
    component Lines: Entity {
        id: lines
        // Flat list of segment end points coordinates: x0, y0, z0, x1, y1, z1, ...
        property var vertices: []
        property color color: "#FFF"

        components: [
            GeometryRenderer {
                primitiveType: GeometryRenderer.Lines
                geometry: Geometry {
                    Attribute {
                        id: linesPosition
                        attributeType: Attribute.VertexAttribute
                        vertexBaseType: Attribute.Float
                        vertexSize: 3
                        count: lines.vertices.length / 3
                        name: defaultPositionAttributeName
                        buffer: Buffer {
                            data: new Float32Array(lines.vertices)
                        }
                    }
                    Attribute {
                        attributeType: Attribute.VertexAttribute
                        vertexBaseType: Attribute.Float
                        vertexSize: 3
                        count: linesPosition.count
                        name: defaultNormalAttributeName
                        buffer: Buffer {
                            data: {
                                var f32 = new Float32Array(linesPosition.count * 3)
                                for (var i = 0; i < linesPosition.count; i++) {
                                    f32[3 * i + 1] = 1.0
                                }
                                return f32
                            }
                        }
                    }
                    boundingVolumePositionAttribute: linesPosition
                }
            },
            // Neutralized Phong: diffuse/specular zeroed so the equation collapses
            // to just `ambient`, giving an unlit-looking constant color. This way
            // the (0,1,0) placeholder normals in the geometry above never affect
            // the final shading, while we stay on the PhongMaterial code path that
            // Metal RHI vertex-descriptor validation is happy with.
            PhongMaterial {
                ambient: lines.color
                diffuse: "#000"
                specular: "#000"
                shininess: 0
            }
        ]
    }

    // Regular grid lines, leaving out the ones lying on the X and Z axes
    Lines {
        vertices: {
            var v = []
            for (var i = gridEntity.first; i <= gridEntity.last; i += gridEntity.offset) {
                if (i === 0)
                    continue
                v.push(i, 0.0, gridEntity.first, i, 0.0, gridEntity.last)
                v.push(gridEntity.first, 0.0, i, gridEntity.last, 0.0, i)
            }
            return v
        }
    }

    // X axis
    Lines {
        vertices: [gridEntity.first, 0.0, 0.0, gridEntity.last, 0.0, 0.0]
        color: Colors.red
    }

    // Z axis (the scene is Y-up, so the grid lies in the XZ plane)
    Lines {
        vertices: [0.0, 0.0, gridEntity.first, 0.0, 0.0, gridEntity.last]
        color: Colors.blue
    }
}
