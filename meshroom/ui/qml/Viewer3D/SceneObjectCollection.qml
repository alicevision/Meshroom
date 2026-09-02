import QtQuick

/**
 * Holds a dynamic collection of MeshObject/MeshLayer and SfmDataObject/SfmDataLayer pairs.
 *
 * Each entry spawns exactly one data object and one rendering layer. Layers are
 * appended to / removed from the target SceneView individually via appendLayer() /
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

    /** Internal models — access via the helper functions below. */
    property ListModel meshModel: ListModel {}
    property ListModel sfmDataModel: ListModel {}

    // ── Internals ─────────────────────────────────────────────────────────────

    /** Return true if @p model already contains an entry with the given source. */
    function _containsSource(model, source) {
        for (var i = 0; i < model.count; ++i) {
            if (model.get(i).source === source)
                return true
        }
        return false
    }

    // ── Mesh helpers ──────────────────────────────────────────────────────────

    /** Append a mesh entry. No-op if @p source is already in the collection. @p label is optional. */
    function addMesh(source, label) {
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
        if (_containsSource(sfmDataModel, source))
        {
            return
        }
        
        sfmDataModel.append({ "source": source, "label": label !== undefined ? label : "" })
    }

    /** Remove the sfmData entry at @p index. */
    function removeSfmData(index) {
        sfmDataModel.remove(index)
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
}
