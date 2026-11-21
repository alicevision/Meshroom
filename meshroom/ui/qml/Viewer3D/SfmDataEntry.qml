import QtQml
import meshViewer

/**
 * LayerList entry pairing a SfmDataObject with its SfmDataLayer.
 * Used by SceneObjectCollection; not intended for direct use.
 */
QtObject {
    id: root

    required property string source
    /** Whether the file is available (e.g. its node is computed): the source is only loaded when ready. */
    required property bool ready
    /** True while waiting for the file to become available. */
    readonly property bool waiting: !ready

    readonly property SfmDataObject dataObject: SfmDataObject {
        source: root.ready ? root.source : ""
    }

    readonly property SfmDataLayer layer: SfmDataLayer {
        sfmData: root.dataObject
        picking: true
    }

    readonly property bool loading: dataObject.loading === true
    /** Non-empty if the last load failed. */
    readonly property string errorString: dataObject.errorString || ""
}
