import QtQuick

/**
 * Holds the 3D objects displayed in a SceneView, as one LayerList per object type.
 *
 * Usage:
 *   SceneObjectCollection {
 *       id: collection
 *       sceneView: sceneView
 *   }
 *   // Then:
 *   collection.meshes.add("file:///path/to/mesh.obj")
 *   collection.sfmData.add("file:///path/to/sfm.abc")
 */
QtObject {
    id: root

    /** Target SceneView to receive layers. */
    property var sceneView: null
    /** SfmDataObject the viewer is looking through, or null for the free camera. */
    property var selectedSfmDataObject: null

    readonly property LayerList meshes: LayerList {
        sceneView: root.sceneView
        typeName: "Mesh"
        delegate: Component {
            MeshEntry {}
        }
    }

    readonly property LayerList sfmData: LayerList {
        sceneView: root.sceneView
        typeName: "SfmData"
        delegate: Component {
            SfmDataEntry {}
        }

        onEntryRemoved: (entry) => {
            if (root.selectedSfmDataObject === entry.dataObject)
            {
                root.selectedSfmDataObject = null
            }
        }
    }

    readonly property LayerList depthmaps: LayerList {
        sceneView: root.sceneView
        typeName: "Depthmap"
        delegate: Component {
            DepthmapEntry {}
        }
    }

    /** Remove all entries from the collection. */
    function clear() {
        selectedSfmDataObject = null
        meshes.clear()
        sfmData.clear()
        depthmaps.clear()
    }

    /** Set the selectedCamera property of every SfmDataLayer in the collection to @p cameraId. */
    function setSelectedCameraForAll(cameraId) {
        for (var i = 0; i < sfmData.count; ++i)
        {
            var entry = sfmData.entryAt(i)
            if (entry)
            {
                entry.layer.selectedCamera = cameraId
            }
        }
    }
}
