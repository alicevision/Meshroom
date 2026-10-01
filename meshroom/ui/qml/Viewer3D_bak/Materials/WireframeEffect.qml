import Qt3D.Core 2.6
import Qt3D.Render 2.6

Effect {
    id: root

    parameters: [
    ]

    techniques: [
        Technique {
            graphicsApiFilter {
                api: GraphicsApiFilter.RHI
                profile: GraphicsApiFilter.CoreProfile
                majorVersion: 1
                minorVersion: 0
            }

            filterKeys: [ FilterKey { name: "renderingStyle"; value: "forward" } ]

            parameters: [
            ]

            renderPasses: [
                RenderPass {
                    shaderProgram: ShaderProgram {
                        vertexShaderCode:   loadSource(Qt.resolvedUrl("shaders/robustwireframe.vert"))
                        fragmentShaderCode: loadSource(Qt.resolvedUrl("shaders/robustwireframe.frag"))
                    }
                }
            ]
        }
    ]
}
