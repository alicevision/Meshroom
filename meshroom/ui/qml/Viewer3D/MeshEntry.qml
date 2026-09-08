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

    property Connections meshLayerConnections: Connections {
        target: root.meshLayer

        function onSelectionChanged() {
            if (typeof _currentScene === "undefined" || !_currentScene) {
                return
            }

            const selectedShapeName = ShapeViewerHelper.selectedShapeName
            if (!selectedShapeName) {
                return
            }

            const observationKey = Point3dViewerHelper.observationKeyForSelectedPoint3d(selectedShapeName)
            if (!observationKey) {
                return
            }

            _currentScene.setObservationFromName(selectedShapeName, observationKey, {
                "X": root.meshLayer.selection.x,
                "Y": root.meshLayer.selection.y,
                "Z": root.meshLayer.selection.z,
                "picked": true
            })
        }
    }
}
