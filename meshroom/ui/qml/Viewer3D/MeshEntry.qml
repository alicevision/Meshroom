import QtQml
import meshViewer

/**
 * Delegate pairing a MeshObject with its MeshLayer.
 * Used by SceneObjectCollection's Instantiator; not intended for direct use.
 */
QtObject {
    id: root

    required property string source

    property MeshObject meshObject: MeshObject {
        source: root.source
    }

    property MeshLayer meshLayer: MeshLayer {
        mesh: root.meshObject
    }
}
