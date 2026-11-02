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
 * An entry added with its source attribute is also removed when that attribute or its node
 * changes (see AttributeWatcher).
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

    /** Attribute each source was added from, if any (kept out of the ListModel, which holds plain values). */
    property var attributeBySource: ({})

    signal entryRemoved(var entry)

    /**
     * Append an entry. No-op if @p source is already in the list.
     * @p label is optional. @p attribute is the optional attribute @p source was read from:
     * the entry is removed when that attribute or its node changes.
     */
    function add(source, label, attribute) {
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

        if (attribute)
        {
            attributeBySource[source] = attribute
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

    /**
     * Remove the entry loaded from @p source on the next event loop iteration, so that an entry is
     * never destroyed while it is emitting a signal.
     */
    function removeSourceLater(source) {
        // A new closure per call: Qt.callLater coalesces calls to the same function, which would
        // only remove the last of several sources invalidated within the same frame
        Qt.callLater(() => removeSource(source))
    }

    /** Remove @p entry if its file failed to load. */
    function handleEntryError(entry) {
        if (!entry.errorString)
        {
            return
        }

        console.warn(`Viewer3D: failed to load ${typeName} "${entry.source}": ${entry.errorString}`)
        removeSourceLater(entry.source)
    }

    function clear() {
        model.clear()
        attributeBySource = {}
    }

    /** Return the entry at @p index, or null if not instantiated (yet). */
    function entryAt(index) {
        return instantiator.objectAt(index)
    }

    readonly property Component attributeWatcher: Component {
        AttributeWatcher {}
    }

    /** Remove @p entry when the attribute it was added from changes. */
    function watchEntryAttribute(entry) {
        const attribute = attributeBySource[entry.source]
        if (!attribute)
        {
            return
        }

        // Parented to the entry: the watcher and its connections are destroyed along with it
        const watcher = attributeWatcher.createObject(entry, { "attribute": attribute, "source": entry.source })
        watcher.invalidated.connect(() => removeSourceLater(entry.source))
    }

    property Instantiator instantiator: Instantiator {
        active: root.sceneView !== null
        model: root.model
        delegate: root.delegate

        onObjectAdded: (index, object) => {
            object.errorStringChanged.connect(() => root.handleEntryError(object))
            root.watchEntryAttribute(object)
            root.sceneView.appendLayer(object.layer)
            root.revision++
        }

        onObjectRemoved: (index, object) => {
            delete root.attributeBySource[object.source]
            root.sceneView.removeLayer(object.layer)
            root.revision++
            root.entryRemoved(object)
        }
    }
}
