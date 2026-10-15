import QtQuick

/**
 * A list of scene objects of one type.
 *
 * Each {source, label} row of @p model is instantiated with @p delegate (MeshEntry, SfmDataEntry, ...),
 * and the entry's layer is appended to / removed from @p sceneView individually, so existing
 * layers and their GPU resources are never disturbed.
 *
 * Entries must expose `source`, `layer`, `dataObject`, `loading` and `errorString`.
 * An entry whose file fails to load (non-empty `errorString`) is removed from the list.
 */
QtObject {
    id: root

    /** Target SceneView to receive layers. Entries are only instantiated once it is set. */
    property var sceneView: null
    property Component delegate: null
    /** Type name used to build fallback labels (e.g. "Mesh"). */
    property string typeName: ""

    readonly property ListModel model: ListModel {}
    readonly property int count: model.count
    /** Incremented whenever an entry is created or destroyed, so that bindings using entryAt() re-evaluate. */
    property int revision: 0

    signal entryRemoved(var entry)

    /** Append an entry. No-op if @p source is already in the list. @p label is optional. */
    function add(source, label) {
        // Coerce to String: @p source may be a QUrl (e.g. from drag-and-drop) or a plain
        // string (e.g. from an attribute value); the ListModel role type must stay consistent.
        source = String(source)

        for (var i = 0; i < model.count; ++i)
        {
            if (model.get(i).source === source)
            {
                return
            }
        }

        model.append({ "source": source, "label": label !== undefined ? label : "" })
    }

    function remove(index) {
        model.remove(index)
    }

    /** Remove the entry loaded from @p source, if any. */
    function removeSource(source) {
        for (var i = 0; i < model.count; ++i)
        {
            if (model.get(i).source === source)
            {
                model.remove(i)
                return
            }
        }
    }

    /** Remove @p entry if its file failed to load. */
    function handleEntryError(entry) {
        if (!entry.errorString)
        {
            return
        }

        console.warn(`Viewer3D: failed to load ${typeName} "${entry.source}": ${entry.errorString}`)
        // Deferred: the entry must not be destroyed while it is emitting the change signal
        Qt.callLater(removeSource, entry.source)
    }

    function clear() {
        model.clear()
    }

    /** Return the entry at @p index, or null if not instantiated (yet). */
    function entryAt(index) {
        return instantiator.objectAt(index)
    }

    property Instantiator instantiator: Instantiator {
        active: root.sceneView !== null
        model: root.model
        delegate: root.delegate

        onObjectAdded: (index, object) => {
            object.errorStringChanged.connect(() => root.handleEntryError(object))
            root.sceneView.appendLayer(object.layer)
            root.revision++
        }

        onObjectRemoved: (index, object) => {
            root.sceneView.removeLayer(object.layer)
            root.revision++
            root.entryRemoved(object)
        }
    }
}
