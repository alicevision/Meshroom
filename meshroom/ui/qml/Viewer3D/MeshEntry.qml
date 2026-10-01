import QtQml
import meshViewer

/**
 * LayerList entry pairing a MeshObject with its MeshLayer.
 * Used by SceneObjectCollection; not intended for direct use.
 */
QtObject {
    id: root

    required property string source

    readonly property MeshObject dataObject: MeshObject {
        source: root.source
    }

    readonly property MeshLayer layer: MeshLayer {
        mesh: root.dataObject
    }

    readonly property bool loading: dataObject.loading === true
}
