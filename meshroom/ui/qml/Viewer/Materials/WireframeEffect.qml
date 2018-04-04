import Qt3D.Core 2.0
import Qt3D.Render 2.0

Effect {
    id: root

    parameters: [
        Parameter { name: "ka";   value: Qt.vector3d( 0.1, 0.1, 0.1 ) },
        Parameter { name: "kd";   value: Qt.vector3d( 0.7, 0.7, 0.7 ) },
        Parameter { name: "ks";  value: Qt.vector3d( 0.95, 0.95, 0.95 ) },
        Parameter { name: "shininess"; value: 150.0 }
    ]

    techniques: [
        Technique {
            graphicsApiFilter {
                api: GraphicsApiFilter.OpenGL
                profile: GraphicsApiFilter.CoreProfile
                majorVersion: 3
                minorVersion: 1
            }

            filterKeys: [ FilterKey { name: "renderingStyle"; value: "forward" } ]

            parameters: [
                Parameter { name: "light.position"; value: Qt.vector4d( 0.0, 0.0, 0.0, 1.0 ) },
                Parameter { name: "light.intensity"; value: Qt.vector3d( 1.0, 1.0, 1.0 ) },
                Parameter { name: "line.width"; value: 1.0 },
                Parameter { name: "line.color"; value: Qt.vector4d( 1.0, 1.0, 1.0, 1.0 ) }
            ]

            renderPasses: [
                RenderPass {
                    shaderProgram: ShaderProgram {
                        vertexShaderCode:   loadSource(Qt.resolvedUrl("shaders/robustwireframe.vert"))
                        geometryShaderCode: loadSource(Qt.resolvedUrl("shaders/robustwireframe.geom"))
                        fragmentShaderCode: loadSource(Qt.resolvedUrl("shaders/robustwireframe.frag"))
                    }
                }
            ]
        }
    ]
}
