import QtQuick 2.9
import Qt3D.Core 2.1


/**
 * MediaLoaderEntity provides a unified interface for accessing statistics
 * of a 3D media independently from the way it was loaded.
 */
Entity {
    property url source

    /// Number of vertices
    property int vertexCount
    /// Number of faces
    property int faceCount
    /// Number of cameras
    property int cameraCount
    /// Number of textures
    property int textureCount
}
