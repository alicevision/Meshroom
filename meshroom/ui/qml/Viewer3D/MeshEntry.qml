import QtQml
import meshViewer

/**
 * LayerList entry pairing a MeshObject with its MeshLayer.
 * Used by SceneObjectCollection; not intended for direct use.
 */
QtObject {
    id: root

    required property string source
    /** Whether the file is available (e.g. its node is computed): the source is only loaded when ready. */
    required property bool ready
    /** True while waiting for the file to become available. */
    readonly property bool waiting: !ready

    readonly property MeshObject dataObject: MeshObject {
        source: root.ready ? root.source : ""
    }

    readonly property MeshLayer layer: MeshLayer {
        mesh: root.dataObject
        picking: true
        shadingMode: MeshLayer.MeshPBR
    }

    readonly property bool loading: dataObject.loading === true
    /** Non-empty if the last load failed. */
    readonly property string errorString: dataObject.errorString || ""
}
