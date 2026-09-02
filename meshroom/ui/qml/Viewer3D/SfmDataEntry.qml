import QtQml
import meshViewer

/**
 * Delegate pairing a SfmDataObject with its SfmDataLayer.
 * Used by SceneObjectCollection's Instantiator; not intended for direct use.
 */
QtObject {
    id: root

    required property string source

    property SfmDataObject sfmDataObject: SfmDataObject {
        source: root.source
    }

    property SfmDataLayer sfmDataLayer: SfmDataLayer {
        sfmData: root.sfmDataObject
    }
}
