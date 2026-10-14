import QtQml
import meshViewer

/**
 * LayerList entry pairing a SfmDataObject with its SfmDataLayer.
 * Used by SceneObjectCollection; not intended for direct use.
 */
QtObject {
    id: root

    required property string source

    readonly property SfmDataObject dataObject: SfmDataObject {
        source: root.source
    }

    readonly property SfmDataLayer layer: SfmDataLayer {
        sfmData: root.dataObject
    }

    readonly property bool loading: dataObject.loading === true
}
