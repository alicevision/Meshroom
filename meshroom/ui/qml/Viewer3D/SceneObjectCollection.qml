import QtQuick

/**
 * Holds a dynamic collection of layers.
 *
 * Layers are appended to / removed from the target SceneView individually via appendLayer() /
 * removeLayer(), so existing layers and their GPU resources are never disturbed.
 *
 * Usage:
 *   SceneObjectCollection {
 *       id: collection
 *       sceneView: sceneView
 *   }
 *   // Then:
 *   collection.addMesh("file:///path/to/mesh.obj")
 *   collection.addSfmData("file:///path/to/sfm.json")
 */
Item {
    id: root

    /** Target SceneView to receive layers. Must be set before any entries are added. */
    property var sceneView: null
    property var selectedSfmDataObject: null

    /** Internal models — access via the helper functions below. */
    property ListModel meshModel: ListModel {}
    property ListModel sfmDataModel: ListModel {}
    property ListModel depthmapModel: ListModel {}

    // ── Internals ─────────────────────────────────────────────────────────────

    /** Return true if @p model already contains an entry with the given source. */
    function _containsSource(model, source) 
    {
        for (var i = 0; i < model.count; ++i) 
        {
            if (model.get(i).source === source)
            {
                return true
            }
        }

        return false
    }

    function setSelectedSfmDataObject(sfmDataObject) 
    {
        if (!sfmDataObject)
        {
            selectedSfmDataObject = null
            return
        }

        selectedSfmDataObject = sfmDataObject
    }

    // ── Depthmap helpers ──────────────────────────────────────────────────────────

    /** Append a depthmap entry. No-op if @p source is already in the collection. @p label is optional. */
    function addDepthmap(source, label) {
        // Coerce to String: @p source may be a QUrl (e.g. from drag-and-drop) or a plain
        // string (e.g. from an attribute value); the ListModel role type must stay consistent.
        source = String(source)

        if (_containsSource(depthmapModel, source))
        {
            return
        }

        depthmapModel.append({ "source": source, "label": label !== undefined ? label : "" })
    }

    /** Remove the depthmap entry at @p index. */
    function removeDepthmap(index) {
        depthmapModel.remove(index)
    }

    /** Return the depthmap at @p index, or null. */
    function depthmapLayerAt(index) {
        var entry = _depthmapInst.objectAt(index)
        return entry ? entry.depthmapLayer : null
    }

    // ── Mesh helpers ──────────────────────────────────────────────────────────

    /** Append a mesh entry. No-op if @p source is already in the collection. @p label is optional. */
    function addMesh(source, label) {
        // Coerce to String: @p source may be a QUrl (e.g. from drag-and-drop) or a plain
        // string (e.g. from an attribute value); the ListModel role type must stay consistent.
        source = String(source)

        if (_containsSource(meshModel, source))
        {
            return
        }

        meshModel.append({ "source": source, "label": label !== undefined ? label : "" })
    }

    /** Remove the mesh entry at @p index. */
    function removeMesh(index) {
        meshModel.remove(index)
    }

    /** Return the MeshObject at @p index, or null. */
    function meshObjectAt(index) {
        var entry = _meshInst.objectAt(index)
        return entry ? entry.meshObject : null
    }

    /** Return the MeshLayer at @p index, or null. */
    function meshLayerAt(index) {
        var entry = _meshInst.objectAt(index)
        return entry ? entry.meshLayer : null
    }

    // ── SfmData helpers ───────────────────────────────────────────────────────

    /** Append an sfmData entry. No-op if @p source is already in the collection. @p label is optional. */
    function addSfmData(source, label) {
        // Coerce to String: @p source may be a QUrl (e.g. from drag-and-drop) or a plain
        // string (e.g. from an attribute value); the ListModel role type must stay consistent.
        source = String(source)

        if (_containsSource(sfmDataModel, source))
        {
            return
        }
        
        sfmDataModel.append({ "source": source, "label": label !== undefined ? label : "" })
    }

    /** Remove the sfmData entry at @p index. */
    function removeSfmData(index) {
        var sfmDataObject = sfmDataObjectAt(index)
        if (selectedSfmDataObject === sfmDataObject)
        {
            selectedSfmDataObject = null
        }

        sfmDataModel.remove(index)
    }

    /** Remove all entries from the collection. */
    function clear() {
        selectedSfmDataObject = null
        meshModel.clear()
        sfmDataModel.clear()
    }

    /** Return the SfmDataObject at @p index, or null. */
    function sfmDataObjectAt(index) {
        var entry = _sfmInst.objectAt(index)
        return entry ? entry.sfmDataObject : null
    }

    /** Return the SfmDataLayer at @p index, or null. */
    function sfmDataLayerAt(index) {
        var entry = _sfmInst.objectAt(index)
        return entry ? entry.sfmDataLayer : null
    }

    /** Set the selectedCamera property of every SfmDataLayer in the collection to @p cameraId. */
    function setSelectedCameraForAll(cameraId) {
        for (var i = 0; i < sfmDataModel.count; ++i) {
            var layer = sfmDataLayerAt(i)
            if (layer) {
                layer.selectedCamera = cameraId
            }
        }
    }

    // ── Internals ─────────────────────────────────────────────────────────────

    Instantiator {
        id: _meshInst
        // Only instantiate once a SceneView is available so onObjectAdded can
        // safely call appendLayer() without a null check at every call site.
        active: root.sceneView !== null
        model: root.meshModel
        delegate: Component {
            MeshEntry {}
        }
        onObjectAdded: (index, object) => root.sceneView.appendLayer(object.meshLayer)
        onObjectRemoved: (index, object) => root.sceneView.removeLayer(object.meshLayer)
    }

    Instantiator {
        id: _sfmInst
        active: root.sceneView !== null
        model: root.sfmDataModel
        delegate: Component {
            SfmDataEntry {}
        }
        onObjectAdded: (index, object) => root.sceneView.appendLayer(object.sfmDataLayer)
        onObjectRemoved: (index, object) => root.sceneView.removeLayer(object.sfmDataLayer)
    }

    Instantiator {
        id: _depthmapInst
        active: root.sceneView !== null
        model: root.depthmapModel
        delegate: Component {
            DepthmapEntry {}
        }
        onObjectAdded: (index, object) => root.sceneView.appendLayer(object.depthmapLayer)
        onObjectRemoved: (index, object) => root.sceneView.removeLayer(object.depthmapLayer)
    }
}
