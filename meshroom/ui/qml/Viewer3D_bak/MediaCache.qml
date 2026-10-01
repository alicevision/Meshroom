import QtQuick
import Qt3D.Core 2.6
import Qt3D.Render 2.6

import Utils 1.0

Entity {
    id: root

    /// Enable debug mode (show cache entity with a scale applied)
    property bool debug: false

    enabled: false  // Disabled entity

    components: [
        Transform {
            id: transform
            scale: 1
        }
    ]

    StateGroup {
        states: [
            State {
                when: root.debug
                name: "debug"
                PropertyChanges {
                    target: root
                    enabled: true
                }
                PropertyChanges {
                    target: transform
                    scale: 0.2
                }
            }
        ]
    }

    property int cacheSize: 2
    property var mediaCache: {[]}

    /// The current number of managed entities
    function currentSize() {
        return Object.keys(mediaCache).length
    }

    /// Whether the cache contains an entity for the given source
    function contains(source) {
        return mediaCache[source] !== undefined
    }

    /// Add an entity to the cache
    function add(source, object) {
        if (!Filepath.exists(source))
            return false
        if (contains(source))
            return true
        if (debug) { console.log("[cache] add: " + source) }
        mediaCache[source] = object
        object.parent = root
        // Remove oldest entry in cache
        if (currentSize() > cacheSize)
            shrink()
        return true
    }

    /// Pop an entity from the cache based on its source
    function pop(source) {
        if (!contains(source))
            return undefined

        var obj = mediaCache[source]
        delete mediaCache[source]
        if (debug) { console.log("[cache] pop: " + source) }
        // Delete cached obj if file does not exist on disk anymore
        if (!Filepath.exists(source)) {
            if (debug) { console.log("[cache] destroy: " + source) }
            obj.destroy()
            obj = undefined
        }
        return obj
    }

    /// Remove and destroy an entity from cache
    function destroyEntity(source) {
        var obj = pop(source)
        if (obj)
            obj.destroy()
    }

    // Shrink cache to fit max size
    function shrink() {
        while (currentSize() > cacheSize)
            destroyEntity(Object.keys(mediaCache)[0])
    }

    // Clear cache and destroy all managed entities
    function clear() {
        Object.keys(mediaCache).forEach(function(key) {
            destroyEntity(key)
        })
    }
}
