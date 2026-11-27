import QtQuick

/**
 * A list of scene objects of one type.
 *
 * Each {source, label, ready} row of @p model is instantiated with @p delegate (MeshEntry, SfmDataEntry, ...),
 * and the entry's layer is appended to / removed from @p sceneView individually, so existing
 * layers and their GPU resources are never disturbed.
 *
 * Entries must expose `source`, `ready`, `layer`, `dataObject`, `loading` and `errorString`, and only
 * load their source while `ready`.
 * An entry whose file fails to load (non-empty `errorString`) is removed from the list.
 * An entry added with its source attribute follows that attribute (see AttributeWatcher): it waits
 * (not ready, unloaded) while the attribute's node is not computed, switches to the new file when the
 * attribute value changes (staying unloaded while the value is empty, e.g. a dynamic output being
 * recomputed), and is removed when the node is removed. If the new file has an extension
 * this list does not load, the entry is removed and entryMoved() is emitted to re-add it elsewhere.
 */
QtObject {
    id: root

    /** Target SceneView to receive layers. Entries are only instantiated once it is set. */
    property var sceneView: null
    property Component delegate: null
    /** Type name used to build fallback labels (e.g. "Mesh"). */
    property string typeName: ""
    /** File extensions (e.g. ".obj") loaded by this list's delegate. */
    property var extensions: []

    readonly property ListModel model: ListModel {}
    readonly property int count: model.count
    /** Incremented whenever an entry is created or destroyed, so that bindings using entryAt() re-evaluate. */
    property int revision: 0

    /** Attribute each source was added from, if any (kept out of the ListModel, which holds plain values). */
    property var attributeBySource: ({})

    /** Attributes currently displayed in the 3D viewer (_currentScene context property), or null when unavailable. */
    readonly property var displayedAttributes: typeof _currentScene === "undefined" || !_currentScene ? null : _currentScene.displayedAttrs3D

    signal entryRemoved(var entry)
    /** Emitted when the attribute of an entry now points to @p source, a file of another type: the entry was removed from this list. */
    signal entryMoved(string source, string label, var attribute)

    /**
     * Append an entry. If @p source is already in the list, only make its layer visible again.
     * @p label is optional. @p attribute is the optional attribute @p source was read from:
     * the entry then waits until the attribute's node is computed, and follows the attribute.
     */
    function add(source, label, attribute) {
        // Coerce to String: @p source may be a QUrl (e.g. from drag-and-drop) or a plain
        // string (e.g. from an attribute value); the ListModel role type must stay consistent.
        source = String(source)

        const index = indexOfSource(source)
        if (index !== -1)
        {
            const entry = entryAt(index)
            if (entry && entry.layer)
            {
                entry.layer.visible = true
            }
            return
        }

        if (attribute)
        {
            attributeBySource[source] = attribute
        }

        // Same test as AttributeWatcher.ready
        const ready = attribute ? Boolean(attribute.node && attribute.node.alive && attribute.node.isComputed) : true
        model.append({ "source": source, "label": label !== undefined ? label : "", "ready": ready })
    }

    /** Return the index of the row loaded from @p source, or -1. */
    function indexOfSource(source) {
        for (var i = 0; i < model.count; ++i)
        {
            if (model.get(i).source === source)
            {
                return i
            }
        }
        return -1
    }

    function remove(index) {
        model.remove(index)
    }

    /** Remove the entry loaded from @p source, if any. */
    function removeSource(source) {
        const index = indexOfSource(source)
        if (index !== -1)
        {
            model.remove(index)
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

    /**
     * Remove (on the next event loop iteration) the entries added from @p attribute, except the one
     * loaded from @p keepSource. Used when a templated attribute is resolved for another view.
     */
    function removeAttributeSourcesLater(attribute, keepSource) {
        keepSource = String(keepSource)
        for (const source in attributeBySource)
        {
            if (source !== keepSource && attributeBySource[source] === attribute)
            {
                removeSourceLater(source)
            }
        }
    }

    /** Remove @p entry if its file failed to load. Errors of entries that are not ready (unloaded) are ignored. */
    function handleEntryError(entry) {
        if (!entry.errorString || !entry.ready)
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

    /** Return the index of the row instantiated as @p entry, or -1 (e.g. if it was removed). */
    function indexOfEntry(entry) {
        for (var i = 0; i < model.count; ++i)
        {
            if (entryAt(i) === entry)
            {
                return i
            }
        }
        return -1
    }

    /**
     * Make @p entry follow the attribute it was added from: update its ready state with the
     * attribute's node, switch to the new file when the attribute value changes, and remove it
     * when the node is removed.
     * The row is looked up by entry: its source is the last file it displayed, which can differ from
     * watcher.source (the last attribute value) while the attribute has no file to display.
     */
    function watchEntryAttribute(entry) {
        const attribute = attributeBySource[entry.source]
        if (!attribute)
        {
            return
        }

        // Parented to the entry: the watcher and its connections are destroyed along with it
        const watcher = attributeWatcher.createObject(entry, { "attribute": attribute, "source": entry.source })
        watcher.readyChanged.connect(() => {
            const index = indexOfEntry(entry)
            if (index !== -1 && !watcher.detached)
            {
                model.setProperty(index, "ready", watcher.ready)
            }
        })
        watcher.nodeRemoved.connect(() => Qt.callLater(() => {
            const index = indexOfEntry(entry)
            if (index !== -1)
            {
                model.remove(index)
            }
        }))
        watcher.attributeValueChanged.connect((newValue) => followAttributeValue(entry, watcher, newValue))
    }

    /**
     * Update @p entry, watched by @p watcher, for @p newValue, the new value of its attribute:
     * - empty (e.g. a dynamic output reset while its node is recomputed): the entry stays, unloaded,
     *   until the attribute points to a file again;
     * - a file of this list: the entry switches to it (and waits for the node to be computed);
     * - templated, already in the list, or of another type: the entry is removed on the next event
     *   loop iteration, and a file of another type is moved to the matching list (see entryMoved).
     * Done synchronously: Graph.update() may set the node back to computed (status read from the cache)
     * right after the value changed, and the entry must not load a stale file meanwhile.
     */
    function followAttributeValue(entry, watcher, newValue) {
        const attribute = watcher.attribute
        if (!attribute.node || !attribute.node.alive)
        {
            return
        }

        const index = indexOfEntry(entry)
        if (index === -1)
        {
            return
        }

        // Each update invalidates the deferred removal scheduled by a previous one
        const generation = ++watcher.generation
        watcher.source = newValue

        // No file for now: stay in the list, unloaded (detached: not reloaded if the node becomes computed)
        if (!newValue)
        {
            watcher.detached = true
            model.setProperty(index, "ready", false)
            return
        }

        const currentSource = model.get(index).source
        const otherIndex = indexOfSource(newValue)
        // Templated paths depend on the view picked in the 2D viewer, resolved by Viewer3D.viewAttribute()
        const dropped = /<\w+>/.test(newValue) || (otherIndex !== -1 && otherIndex !== index)
        const moved = !dropped && extensions.indexOf(Filepath.extension(newValue)) === -1
        if (dropped || moved)
        {
            const label = model.get(index).label
            // Unload now and remove later: never destroy the entry while its watcher emits a signal.
            // attributeBySource is left untouched: onObjectRemoved uses it to clean up displayedAttributes.
            watcher.detached = true
            model.setProperty(index, "ready", false)
            Qt.callLater(() => {
                const row = indexOfEntry(entry)
                // Already removed, or superseded by a later update (the row exists, so its watcher too)
                if (row === -1 || watcher.generation !== generation)
                {
                    return
                }
                model.remove(row)
                // Input edges of a removed node are disconnected before the node is flagged as not alive:
                // only move the entry if its node still exists
                if (moved && attribute.node && attribute.node.alive)
                {
                    entryMoved(newValue, label, attribute)
                }
            })
            return
        }

        watcher.detached = false
        if (newValue !== currentSource)
        {
            delete attributeBySource[currentSource]
            attributeBySource[newValue] = attribute
            // Unload before switching the source, so the previous file is never reloaded
            model.setProperty(index, "ready", false)
            model.setProperty(index, "source", newValue)
        }
        model.setProperty(index, "ready", watcher.ready)
    }

    property Instantiator instantiator: Instantiator {
        active: root.sceneView !== null
        model: root.model
        delegate: root.delegate

        onObjectAdded: (index, object) => {
            object.errorStringChanged.connect(() => root.handleEntryError(object))
            root.watchEntryAttribute(object)
            // Flag the source attribute as displayed (visibility icon in the attribute editor).
            // The model allows duplicates, so an attribute stays flagged while any of its entries remains.
            const attribute = root.attributeBySource[object.source]
            if (attribute && root.displayedAttributes)
            {
                root.displayedAttributes.append(attribute)
            }
            root.sceneView.appendLayer(object.layer)
            root.revision++
        }

        onObjectRemoved: (index, object) => {
            const attribute = root.attributeBySource[object.source]
            if (attribute && root.displayedAttributes && root.displayedAttributes.contains(attribute))
            {
                root.displayedAttributes.remove(attribute)
            }
            delete root.attributeBySource[object.source]
            root.sceneView.removeLayer(object.layer)
            root.revision++
            root.entryRemoved(object)
        }
    }
}
