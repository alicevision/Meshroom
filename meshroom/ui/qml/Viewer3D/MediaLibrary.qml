import QtQuick 2.9
import Qt3D.Core 2.1
import Qt3D.Render 2.1
import Utils 1.0


/**
 * MediaLibrary is an Entity that loads and manages a list of 3D media.
 * It also uses an internal cache to instantly reload media.
 */
Entity {
    id: root

    readonly property alias model: m.mediaModel
    property int renderMode
    property bool pickingEnabled: false
    readonly property alias count: instantiator.count // number of instantiated media delegates

    /// Camera to consider for positionning
    property Camera camera: null

    /// True while at least one media is being loaded
    readonly property bool loading: {
        for(var i=0; i<m.mediaModel.count; ++i) {
            if(m.mediaModel.get(i).status === SceneLoader.Loading)
                return true;
        }
        return false;
    }

    signal pressed(var pick)
    signal loadRequest(var idx)

    QtObject {
        id: m
        property ListModel mediaModel: ListModel { dynamicRoles: true }
        property var sourceToEntity: ({})

        readonly property var mediaElement: ({
            "source": "",
            "valid": true,
            "label": "",
            "visible": true,
            "section": "",
            "attribute": null,
            "entity": null,
            "requested": true,
            "vertexCount": 0,
            "faceCount": 0,
            "cameraCount": 0,
            "textureCount": 0,
            "status": SceneLoader.None
        })
    }

    function makeElement(values) {
        return Object.assign({}, JSON.parse(JSON.stringify(m.mediaElement)), values);
    }

    function ensureVisible(source) {
        var idx = find(source);
        if(idx === -1)
            return
        m.mediaModel.get(idx).visible = true;
        loadRequest(idx);
    }

    function find(source) {
        for(var i=0; i<m.mediaModel.count; ++i) {
            var elt = m.mediaModel.get(i);
            if( elt.source === source || elt.attribute === source)
                return i;
        }
        return -1;
    }

    function load(filepath) {
        var pathStr = Filepath.urlToString(filepath);
        if(!Filepath.exists(pathStr))
        {
            console.warn("Media Error: File " + pathStr + " does not exist.");
            return;
        }
        // file already loaded, return
        if(m.sourceToEntity[pathStr]) {
            ensureVisible(pathStr);
            return;
        }

        // add file to the internal ListModel
        m.mediaModel.append(makeElement({
                    "source": pathStr,
                    "label": Filepath.basename(pathStr),
                    "section": "External"
        }));
    }


    function view(attribute) {
        if(m.sourceToEntity[attribute]) {
            ensureVisible(attribute);
            return;
        }

        var attrLabel = attribute.isOutput ? "" : attribute.fullName.replace(attribute.node.name, "");
        var section = attribute.node.label;
        // add file to the internal ListModel
        m.mediaModel.append(makeElement({
                "label": section + attrLabel,
                "section": section,
                "attribute": attribute,
        }));
    }

    function remove(index) {
        // remove corresponding entry from model
        m.mediaModel.remove(index);
    }

    /// Get entity based on source
    function entity(source) {
        return sourceToEntity[source];
    }

    function entityAt(index) {
        return instantiator.objectAt(index);
    }

    function solo(index) {
        for(var i=0; i<m.mediaModel.count; ++i) {
            m.mediaModel.setProperty(i, "visible", i === index);
        }
    }

    function clear() {
        m.mediaModel.clear();
        cache.clear();
    }

    // Cache that keeps in memory the last unloaded 3D media
    MediaCache {
        id: cache
    }

    NodeInstantiator {
        id: instantiator
        model: m.mediaModel

        delegate: MediaLoader {
            id: mediaLoader

            // whether MediaLoader has been fully instantiated by the NodeInstantiator
            property bool fullyInstantiated: false

            // explicitely store some attached model properties for outside use and ease binding
            readonly property var attribute: model.attribute
            readonly property int idx: index
            readonly property var modelSource: attribute || model.source
            readonly property bool visible: model.visible

            // multi-step binding to ensure MediaLoader source is properly
            // updated when needed, whether raw source is valid or not

            // raw source path
            readonly property string rawSource: attribute ? attribute.value : model.source
            // whether dependencies are statified (applies for output/connected input attributes only)
            readonly property bool dependencyReady: {
                if(attribute && attribute.isOutput)
                    return attribute.node.globalStatus === "SUCCESS";
                if(attribute && attribute.isLink)
                    return attribute.linkParam.node.globalStatus === "SUCCESS";
                return true;
            }
            // source based on raw source + dependency status
            readonly property string currentSource: dependencyReady ? rawSource : ""
            // source based on currentSource + "requested" property
            readonly property string finalSource: model.requested ? currentSource : ""

            camera: root.camera
            renderMode: root.renderMode
            enabled: visible

            // QObject.destroyed signal is not accessible
            // Use the object as NodeInstantiator model to be notified of its deletion
            NodeInstantiator {
                model: attribute
                delegate: Entity { objectName: "DestructionWatcher [" + attribute.toString() + "]" }
                onObjectRemoved: remove(idx)
            }

            // 'visible' property drives media loading request
            onVisibleChanged: {
                // always request media loading if visible
                if(model.visible)
                    model.requested = true;
                // only cancel loading request if media is not valid
                // (a media won't be unloaded if already loaded, only hidden)
                else if(!model.valid)
                    model.requested = false;
            }

            function updateCacheAndModel(forceRequest) {
                // don't cache explicitely unloaded media
                if(model.requested && object && dependencyReady) {
                    // cache current object
                    if(cache.add(Filepath.urlToString(mediaLoader.source), object));
                        object = null;
                }
                updateModel(forceRequest);
            }

            function updateModel(forceRequest) {
                // update model's source path if input is an attribute
                if(attribute) {
                    model.source = rawSource;
                }
                // auto-restore entity if raw source is in cache
                model.requested = forceRequest || (!model.valid && model.requested) || cache.contains(rawSource);
                model.valid = Filepath.exists(rawSource) && dependencyReady;
            }

            Component.onCompleted: {
                // keep 'source' -> 'entity' reference
                m.sourceToEntity[modelSource] = mediaLoader;
                // always request media loading when delegate has been created
                updateModel(true);
                // if external media failed to open, remove element from model
                if(!attribute && !object)
                    remove(index)
            }

            onCurrentSourceChanged: {
                updateCacheAndModel(false)
            }

            onFinalSourceChanged: {
                // update media visibility
                // (useful if media was explicitly unloaded or hidden but loaded back from cache)
                model.visible = model.requested;

                var cachedObject = cache.pop(rawSource);
                cached = cachedObject !== undefined;
                if(cached) {
                    object = cachedObject;
                    // only change cached object parent if mediaLoader has been fully instantiated
                    // by the NodeInstantiator; otherwise re-parenting will fail silently and the object will disappear...
                    // see "onFullyInstantiatedChanged" and parent NodeInstantiator's "onObjectAdded"
                    if(fullyInstantiated) {
                        object.parent = mediaLoader;
                    }
                }
                mediaLoader.source = Filepath.stringToUrl(finalSource);
                if(object) {
                    // bind media info to corresponding model roles
                    // (test for object validity to avoid error messages right after object has been deleted)
                    var boundProperties = ["vertexCount", "faceCount", "cameraCount", "textureCount"];
                    boundProperties.forEach( function(prop){
                        model[prop] = Qt.binding(function() { return object ? object[prop] : 0; });
                    })
                }
                else if(finalSource) {
                    // source was valid but no loader was created, remove element
                    remove(index);
                }
            }

            onFullyInstantiatedChanged: {
                // delayed reparenting of object coming from the cache
                if(object)
                    object.parent = mediaLoader;
            }

            onStatusChanged: {
                model.status = status
                // remove model entry for external media that failed to load
                if(status === SceneLoader.Error && !model.attribute)
                    remove(index);
            }

            components: [
                ObjectPicker {
                    enabled: mediaLoader.enabled && pickingEnabled
                    hoverEnabled: false
                    onPressed: root.pressed(pick)
                }
            ]
        }

        onObjectAdded: {
            // notify object that it is now fully instantiated
            object.fullyInstantiated = true;
        }

        onObjectRemoved: {
            delete m.sourceToEntity[object.modelSource];
        }
    }
}
