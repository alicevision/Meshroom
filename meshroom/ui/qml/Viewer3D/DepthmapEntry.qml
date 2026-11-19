import QtQml
import meshViewer

/**
 * LayerList entry holding a DepthmapLayer (which loads its own data, hence no dataObject).
 * Used by SceneObjectCollection; not intended for direct use.
 */
QtObject {
    id: root

    required property string source
    /** Whether the file is available (e.g. its node is computed): the source is only loaded when ready. */
    required property bool ready
    /** True while waiting for the file to become available. */
    readonly property bool waiting: !ready

    readonly property var dataObject: null

    readonly property DepthmapLayer layer: DepthmapLayer {
        source: root.ready ? root.source : ""
    }

    readonly property bool loading: layer.loading === true
    /** Non-empty if the last load failed. */
    readonly property string errorString: layer.errorString || ""
}
