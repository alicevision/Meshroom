import QtQml
import meshViewer

/**
 * LayerList entry holding a DepthmapLayer (which loads its own data, hence no dataObject).
 * Used by SceneObjectCollection; not intended for direct use.
 */
QtObject {
    id: root

    required property string source

    readonly property var dataObject: null

    readonly property DepthmapLayer layer: DepthmapLayer {
        source: root.source
    }

    readonly property bool loading: layer.loading === true
}
