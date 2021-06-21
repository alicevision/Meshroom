import AliceVisionImageIO 1.0 as AliceVisionImageIO

/**
 * Support for Depth Map files (EXR) in Qt3d.
 * Create this component dynamically to test for DepthMapEntity plugin availability.
 */
AliceVisionImageIO.DepthMapEntity {
    id: root

    pointSize: Viewer3DSettings.pointSize * (Viewer3DSettings.fixedPointSize ? 1.0 : 0.001)
    // map render modes to custom visualization modes
    displayMode: Viewer3DSettings.renderMode == 1 ? AliceVisionImageIO.DepthMapEntity.Points : AliceVisionImageIO.DepthMapEntity.Triangles
    displayColor: Viewer3DSettings.renderMode == 2
}
