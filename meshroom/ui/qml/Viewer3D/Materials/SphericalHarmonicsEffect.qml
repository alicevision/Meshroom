import Qt3D.Core 2.6
import Qt3D.Render 2.6

Effect {
    id: root


    parameters: [
        Parameter { name: "shCoeffs[0]"; value: [] },
        Parameter { name: "displayNormals"; value: false }
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

            renderPasses: [
                RenderPass {
                    shaderProgram: ShaderProgram {
                        vertexShaderCode:   loadSource(Qt.resolvedUrl("shaders/SphericalHarmonics.vert"))
                        fragmentShaderCode: loadSource(Qt.resolvedUrl("shaders/SphericalHarmonics.frag"))

                    }
                }
            ]
        }
    ]
}
