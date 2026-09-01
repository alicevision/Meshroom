import QtQuick
import Qt3D.Core 2.6

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
    /// Number of resection IDs
    property int resectionIdCount
    /// Current resection ID
    property int resectionId
    /// Groups of cameras based on resection IDs
    property var resectionGroups
}
