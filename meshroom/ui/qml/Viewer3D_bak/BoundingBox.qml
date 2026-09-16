import Qt3D.Core 2.6
import Qt3D.Render 2.6
import Qt3D.Input 2.6
import Qt3D.Extras 2.15
import QtQuick

Entity {
    id: root
    property Transform transform: Transform {}

    components: [transform]

    Entity {
        components: [cube, greyMaterial]

        CuboidMesh {
            id: cube
            property real edge : 1.995  // Almost 2: important to have all the cube's vertices with a unit of 1
            xExtent: edge
            yExtent: edge
            zExtent: edge
        }
        PhongAlphaMaterial {
            id: greyMaterial
            property color base: "#fff"
            ambient: base
            alpha: 0.15

            // Pretty convincing combination
            blendFunctionArg: BlendEquation.Add
            sourceRgbArg: BlendEquationArguments.SourceAlpha
            sourceAlphaArg: BlendEquationArguments.OneMinusSourceAlpha
            destinationRgbArg: BlendEquationArguments.DestinationColor
            destinationAlphaArg: BlendEquationArguments.OneMinusSourceAlpha
        }
    }

    Entity {
        components: [edges, orangeMaterial]

        // Neutralized Phong: diffuse/specular zeroed so the equation collapses
        // to just `ambient`, giving an unlit-looking constant color. This way
        // the (0,1,0) placeholder normals in the geometry below never affect
        // the final shading, while we stay on the PhongMaterial code path that
        // Metal RHI vertex-descriptor validation is happy with.
        PhongMaterial {
            id: orangeMaterial
            property color base: "#f49b2b"
            ambient: base
            diffuse: "#000"
            specular: "#000"
            shininess: 0
        }

        GeometryRenderer {
            id: edges
            primitiveType: GeometryRenderer.Lines
            geometry: Geometry {
                Attribute {
                    id: boundingBoxPosition
                    attributeType: Attribute.VertexAttribute
                    vertexBaseType: Attribute.Float
                    vertexSize: 3
                    count: 24
                    name: defaultPositionAttributeName
                    buffer: Buffer {
                        data: new Float32Array([
                            1.0, 1.0, 1.0,
                            1.0, -1.0, 1.0,
                            1.0, 1.0, 1.0,
                            1.0, 1.0, -1.0,
                            1.0, 1.0, 1.0,
                            -1.0, 1.0, 1.0,
                            -1.0, -1.0, -1.0,
                            -1.0, 1.0, -1.0,
                            -1.0, -1.0, -1.0,
                            1.0, -1.0, -1.0,
                            -1.0, -1.0, -1.0,
                            -1.0, -1.0, 1.0,
                            1.0, -1.0, 1.0,
                            1.0, -1.0, -1.0,
                            1.0, 1.0, -1.0,
                            1.0, -1.0, -1.0,
                            -1.0, 1.0, 1.0,
                            -1.0, 1.0, -1.0,
                            1.0, -1.0, 1.0,
                            -1.0, -1.0, 1.0,
                            -1.0, 1.0, 1.0,
                            -1.0, -1.0, 1.0,
                            -1.0, 1.0, -1.0,
                            1.0, 1.0, -1.0
                            ])
                    }
                }
                Attribute {
                    attributeType: Attribute.VertexAttribute
                    vertexBaseType: Attribute.Float
                    vertexSize: 3
                    count: 24
                    name: defaultNormalAttributeName
                    buffer: Buffer {
                        data: {
                            var f32 = new Float32Array(24 * 3)
                            for (var i = 0; i < 24; i++) {
                                f32[3 * i] = 0.0
                                f32[3 * i + 1] = 1.0
                                f32[3 * i + 2] = 0.0
                            }
                            return f32
                        }
                    }
                }
                boundingVolumePositionAttribute: boundingBoxPosition
            }
        }
    }
}
