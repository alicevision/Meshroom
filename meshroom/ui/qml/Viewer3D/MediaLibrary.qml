import QtQuick
import Qt3D.Core 2.6
import Qt3D.Render 2.6

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
    readonly property alias count: instantiator.count  // Number of instantiated media delegates

    // For TransformGizmo in BoundingBox
    property DefaultCameraController sceneCameraController
    property Layer frontLayerComponent
    property var window

    /// Camera to consider for positioning
    property Camera camera: null

    /// True while at least one media is being loaded
    readonly property bool loading: {
        for (var i = 0; i < m.mediaModel.count; ++i) {
            if (m.mediaModel.get(i).status === SceneLoader.Loading)
                return true
        }
        return false
    }

    signal clicked(var pick)
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
            "hasBoundingBox": false,  // For Meshing node only
            "displayBoundingBox": true,  // For Meshing node only
            "hasTransform": false,  // For SfMTransform node only
            "displayTransform": true,  // For SfMTransform node only
            "section": "",
            "attribute": null,
            "entity": null,
            "requested": true,
            "vertexCount": 0,
            "faceCount": 0,
            "cameraCount": 0,
            "textureCount": 0,
            "resectionIdCount": 0,
            "resectionId": 0,
            "resectionGroups": [],
            "status": SceneLoader.None
        })
    }

    function makeElement(values) {
        return Object.assign({}, JSON.parse(JSON.stringify(m.mediaElement)), values)
    }

    function ensureVisible(source) {
        var idx = find(source)
        if (idx === -1)
            return
        m.mediaModel.get(idx).visible = true
        loadRequest(idx)
    }

    function find(source) {
        for (var i = 0; i < m.mediaModel.count; ++i) {
            var elt = m.mediaModel.get(i)
            if (elt.source === source || elt.attribute === source)
                return i
        }
        return -1
    }

    function load(filepath, label = undefined) {
        var pathStr = Filepath.urlToString(filepath)
        if (!Filepath.exists(pathStr)) {
            console.warn("Media Error: File " + pathStr + " does not exist.")
            return
        }
        // File already loaded, return
        if (m.sourceToEntity[pathStr]) {
            ensureVisible(pathStr)
            return
        }

        // Add file to the internal ListModel
        m.mediaModel.append(
            makeElement({
                "source": pathStr,
                "label": label ? label : Filepath.basename(pathStr),
                "section": "External"
        }))
    }

    function view(attribute) {
        if (m.sourceToEntity[attribute]) {
            ensureVisible(attribute)
            return
        }

        var attrLabel = attribute.isOutput ? "" : attribute.fullName.replace(attribute.node.name, "")
        var section = attribute.node.label
        // Add file to the internal ListModel
        m.mediaModel.append(
            makeElement({
                "label": section + attrLabel,
                "section": section,
                "attribute": attribute
        }))
    }

    function remove(index) {
        // Remove corresponding entry from model
        m.mediaModel.remove(index)
    }

    /// Get entity based on source
    function entity(source) {
        return sourceToEntity[source]
    }

    function entityAt(index) {
        return instantiator.objectAt(index)
    }

    function solo(index) {
        for (var i = 0; i < m.mediaModel.count; ++i) {
            m.mediaModel.setProperty(i, "visible", i === index)
        }
    }

    function clear() {
        m.mediaModel.clear()
        cache.clear()
    }

    // Cache that keeps in memory the last unloaded 3D media
    MediaCache {
        id: cache
    }

    NodeInstantiator {
        id: instantiator
        model: m.mediaModel

        delegate: Entity {
            id: instantiatedEntity
            property alias fullyInstantiated: mediaLoader.fullyInstantiated
            readonly property alias modelSource: mediaLoader.modelSource

            // Get the node
            property var currentNode: model.attribute ? model.attribute.node : null
            property string nodeType: currentNode ? currentNode.nodeType: null

            // Specific properties to the MESHING node (declared and initialized for every Entity anyway)
            property bool hasBoundingBox: {
                if (currentNode && currentNode.hasAttribute("useBoundingBox")) // Can have a BoundingBox
                    return currentNode.attribute("useBoundingBox").value
                return false
            }
            onHasBoundingBoxChanged: model.hasBoundingBox = hasBoundingBox
            property bool displayBoundingBox: model.displayBoundingBox

            // Specific properties to the SFMTRANSFORM node (declared and initialized for every Entity anyway)
            property bool hasTransform: {
                if (nodeType === "SfMTransform" && currentNode.attribute("method")) // Can have a Transform
                    return currentNode.attribute("method").value === "manual"
                return false
            }
            onHasTransformChanged: model.hasTransform = hasTransform
            property bool displayTransform: model.displayTransform


            // Create the medias
            MediaLoader {
                id: mediaLoader

                cameraPickingEnabled: !sceneCameraController.pickingActive

                // Whether MediaLoader has been fully instantiated by the NodeInstantiator
                property bool fullyInstantiated: false

                // Explicitly store some attached model properties for outside use and ease binding
                readonly property var attribute: model.attribute
                readonly property int idx: index
                readonly property var modelSource: attribute || model.source
                readonly property bool visible: model.visible

                // Multi-step binding to ensure MediaLoader source is properly
                // updated when needed, whether raw source is valid or not

                // Raw source path
                property string rawSource: attribute ? attribute.value : model.source
                // Whether dependencies are statified (applies for output/connected input attributes only)
                readonly property bool dependencyReady: {
                    if (attribute) {
                        const rootAttribute = attribute.isLink ? attribute.rootLinkParam : attribute
                        if (rootAttribute.isOutput)
                            return rootAttribute.node.globalStatus === "SUCCESS"
                    }
                    return true  // Is an input param without link (so no dependency) or an external file
                }
                // Source based on raw source + dependency status
                property string currentSource: dependencyReady ? rawSource : ""
                // Source based on currentSource + "requested" property
                property string finalSource: model.requested ? currentSource : ""

                // To use only if we want to draw the input source and not the current node output (Warning: to use with caution)
                // There is maybe a better way to do this to avoid overwriting bindings which should be readonly properties
                function drawInputSource() {
                    rawSource = Qt.binding(() => instantiatedEntity.currentNode ? instantiatedEntity.currentNode.attribute("input").value: "")
                    currentSource = Qt.binding(() => rawSource)
                    finalSource = Qt.binding(() => rawSource)
                }

                camera: root.camera
                renderMode: root.renderMode
                enabled: visible

                property bool alive: attribute ? attribute.node.alive : false
                onAliveChanged: {
                    if (!alive && index >= 0)
                          remove(index)
                }

                // 'visible' property drives media loading request
                onVisibleChanged: {
                    // Always request media loading if visible
                    if (model.visible)
                        model.requested = true
                    // Only cancel loading request if media is not valid
                    // (a media won't be unloaded if already loaded, only hidden)
                    else if (!model.valid)
                        model.requested = false
                }

                function updateCacheAndModel(forceRequest) {
                    // Don't cache explicitly unloaded media
                    if (model.requested && object && dependencyReady) {
                        // Cache current object
                        if (cache.add(Filepath.urlToString(mediaLoader.source), object))
                            object = null
                    }
                    updateModel(forceRequest)
                }

                function updateModel(forceRequest) {
                    // Update model's source path if input is an attribute
                    if (attribute) {
                        model.source = rawSource
                    }
                    // Auto-restore entity if raw source is in cache
                    model.requested = forceRequest || (!model.valid && model.requested) || cache.contains(rawSource)
                    model.valid = Filepath.exists(rawSource) && dependencyReady
                }

                Component.onCompleted: {
                    // Keep 'source' -> 'entity' reference
                    m.sourceToEntity[modelSource] = instantiatedEntity
                    // Always request media loading when delegate has been created
                    updateModel(true)
                    // If external media failed to open, remove element from model
                    if (!attribute && !object)
                        remove(index)
                }

                onCurrentSourceChanged: {
                    updateCacheAndModel(false)

                    // Avoid the bounding box to disappear when we move it after a mesh already computed
                    if (instantiatedEntity.hasBoundingBox && !currentSource)
                        model.visible = true
                }

                onFinalSourceChanged: {
                    // Update media visibility
                    // (useful if media was explicitly unloaded or hidden but loaded back from cache)
                    model.visible = model.requested

                    var cachedObject = cache.pop(rawSource)
                    cached = cachedObject !== undefined
                    if (cached) {
                        object = cachedObject
                        // Only change cached object parent if mediaLoader has been fully instantiated
                        // by the NodeInstantiator; otherwise re-parenting will fail silently and the object will disappear...
                        // see "onFullyInstantiatedChanged" and parent NodeInstantiator's "onObjectAdded"
                        if (fullyInstantiated) {
                            object.parent = mediaLoader
                        }
                    }
                    mediaLoader.source = Filepath.stringToUrl(finalSource)
                    if (object) {
                        // Bind media info to corresponding model roles
                        // (test for object validity to avoid error messages right after object has been deleted)
                        var boundProperties = ["vertexCount", "faceCount", "cameraCount", "textureCount", "resectionIdCount", "resectionId", "resectionGroups"]
                        boundProperties.forEach(function(prop) {
                            model[prop] = Qt.binding(function() { return object ? object[prop] : 0 })
                        })
                    } else if (finalSource && status === Component.Ready) {
                        // Source was valid but no loader was created, remove element
                        // Check if component is ready to avoid removing element from the model before adding instance to the node
                        remove(index)
                    }
                }

                onFullyInstantiatedChanged: {
                    // Delayed reparenting of object coming from the cache
                    if (object)
                        object.parent = mediaLoader
                }

                onStatusChanged: {
                    model.status = status
                    // Remove model entry for external media that failed to load
                    if (status === SceneLoader.Error && !model.attribute)
                        remove(index)
                }

                components: [
                    ObjectPicker {
                        enabled: mediaLoader.enabled && pickingEnabled
                        hoverEnabled: false
                        onClicked: function(pick) { root.clicked(pick) }
                    }
                ]
            }

            // Transform: display a TransformGizmo for SfMTransform node only
            // Note: use a NodeInstantiator to evaluate if the current node is a SfMTransform node and if the transform mode is set to Manual
            NodeInstantiator {
                id: sfmTransformGizmoInstantiator
                active: instantiatedEntity.hasTransform
                model: 1

                SfMTransformGizmo {
                    id: sfmTransformGizmoEntity
                    sceneCameraController: root.sceneCameraController
                    frontLayerComponent: root.frontLayerComponent
                    window: root.window
                    currentSfMTransformNode: instantiatedEntity.currentNode
                    enabled: mediaLoader.visible && instantiatedEntity.displayTransform

                    Component.onCompleted: {
                        mediaLoader.drawInputSource()  // Because we are sure we want to show the input in MANUAL mode only
                        Scene3DHelper.addComponent(mediaLoader, sfmTransformGizmoEntity.objectTransform)  // Add the transform to the media to see real-time transformations
                    }
                }
            }

            // BoundingBox: display bounding box for MESHING computation
            // Note: use a NodeInstantiator to evaluate if the current node is a MESHING node and if the checkbox is active
            NodeInstantiator {
                id: boundingBoxInstantiator
                active: instantiatedEntity.hasBoundingBox
                model: 1

                MeshingBoundingBox {
                    sceneCameraController: root.sceneCameraController
                    frontLayerComponent: root.frontLayerComponent
                    window: root.window
                    currentMeshingNode: instantiatedEntity.currentNode
                    enabled: mediaLoader.visible && instantiatedEntity.displayBoundingBox
                }
            }
        }

        onObjectAdded: function(index, object) {
            // Notify object that it is now fully instantiated
            object.fullyInstantiated = true
        }

        onObjectRemoved: function(index, object) {
            if (m.sourceToEntity[object.modelSource])
                delete m.sourceToEntity[object.modelSource]
        }
    }
}
