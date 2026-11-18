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
 *   // Removed when the attribute or its node changes:
 *   collection.sfmData.add(attribute.value, "SfM", attribute)
 */
QtObject {
    id: root

    /** Target SceneView to receive layers. */
    property var sceneView: null
    /** SfmDataObject the viewer is looking through, or null for the free camera. */
    property var selectedSfmDataObject: null
    /** Node whose "boundingBox" attribute is edited in the viewer (e.g. Meshing), or null. */
    property var boundingBoxNode: null
    /** Whether the user wants the bounding box of boundingBoxNode displayed. */
    property bool showBoundingBox: true
    /** Multiplier applied to the free camera zoom (wheel and right drag). */
    property real zoomSpeed: 1.0

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
        boundingBoxNode = null
        meshes.clear()
        sfmData.clear()
        depthmaps.clear()
    }

    /**
     * Set the visibility of the layers whose visibility is set from the 3D inspector: the image layer
     * and the entries of meshes, sfmData and depthmaps.
     * Helper layers (grid, axis, bounding box, survey points) are left unchanged.
     * @p isVisible(layer, attribute) returns whether a layer is shown; attribute is the one the layer
     * was loaded from, or undefined.
     */
    function setLayersVisibility(isVisible) {
        for (const layerList of [meshes, sfmData, depthmaps])
        {
            for (var i = 0; i < layerList.count; ++i)
            {
                const entry = layerList.entryAt(i)
                if (entry)
                {
                    entry.layer.visible = isVisible(entry.layer, layerList.attributeBySource[entry.source])
                }
            }
        }

        const imageLayer = sceneView ? sceneView.imageLayerRef : null
        if (imageLayer)
        {
            imageLayer.visible = isVisible(imageLayer, undefined)
        }
    }

    /** Show @p layer and hide the others (see setLayersVisibility). */
    function showOnly(layer) {
        setLayersVisibility((otherLayer) => otherLayer === layer)
    }

    /** Show the layers loaded from the attributes of @p node and hide the others (see setLayersVisibility). */
    function showOnlyNode(node) {
        setLayersVisibility((layer, attribute) => attribute !== undefined && attribute.node === node)
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
