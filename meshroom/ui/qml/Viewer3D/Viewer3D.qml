import meshViewer

import QtQuick
import QtQuick.Controls
import Utils 1.0

Item {
    id: root

    property alias collection: collection

    // Current scene (_currentScene context property), or null when unavailable
    readonly property var scene: typeof _currentScene === "undefined" ? null : _currentScene
    // Active orbit motion, or null while looking through an SfM camera
    readonly property var orbit: sceneView.motionInfo instanceof OrbitMotionInfo ? sceneView.motionInfo : null
    // Name of the shape selected alone (empty for no or a multiple selection), target of the survey point picking
    readonly property string selectedShapeName: ShapeViewerHelper.selectedShapeNames.length === 1 ? ShapeViewerHelper.selectedShapeNames[0] : ""

    // Sentinel used by SfmDataLayer.selectedCamera to mean "no camera selected" (UndefinedIndexT).
    // Declared as "var" (not "int") since QML's int is 32-bit signed and would overflow 0xFFFFFFFF to -1.
    readonly property var invalidCameraId: 0xFFFFFFFF

    // OrbitMotionInfo view presets triggered by numpad keys
    readonly property var numpadViews: ({
        [Qt.Key_8]: "viewTop",
        [Qt.Key_2]: "viewBottom",
        [Qt.Key_5]: "viewFront",
        [Qt.Key_7]: "viewBack",
        [Qt.Key_4]: "viewLeft",
        [Qt.Key_6]: "viewRight"
    })

    // LayerList receiving each supported file extension
    readonly property var layerListByExtension: ({
        ".abc": collection.sfmData,
        ".usda": collection.sfmData,
        ".sfm": collection.sfmData,
        ".obj": collection.meshes,
        ".glb": collection.meshes,
        ".exr": collection.depthmaps
    })

    focus: true

    Keys.onPressed: function(event) {
        const isNumpad = (event.modifiers & Qt.KeypadModifier) !== 0

        let action = null
        
        if (event.key === Qt.Key_Z)
        {
            action = () => orbit.setDistance(1.0)
        }
        else if (event.key === Qt.Key_K)
        {
            action = () => orbit.fit(sceneView.boundingBox)
        }
        else if (isNumpad && event.key === Qt.Key_Period)
        {
            action = () => { fallbackCameraInfo.orthographic = !fallbackCameraInfo.orthographic }
        }
        else if (isNumpad && numpadViews[event.key])
        {
            action = () => orbit[numpadViews[event.key]]()
        }

        if (!action)
        {
            return
        }

        if (orbit)
        {
            action()
        }

        event.accepted = true
    }

    function isValidSelectedViewId(viewId)
    {
        if (viewId === undefined || viewId === null)
        {
            return false
        }

        const normalizedViewId = String(viewId)
        return normalizedViewId.length > 0 && normalizedViewId !== "-1"
    }

    function isValidCameraId(cameraId)
    {
        return cameraId !== undefined && cameraId !== null && cameraId !== invalidCameraId
    }

    function syncSelectedCameraToScene(layer)
    {
        if (scene && isValidCameraId(layer.selectedCamera))
        {
            scene.selectedViewId = String(layer.selectedCamera)
        }
    }

    /**
     * Move the free camera (which must be the current sceneView motion) to the orbit pose closest to the
     * view matrix @p view (world to camera, looking along -Z): same position and viewing direction,
     * without roll since the orbit keeps the world Y axis up.
     * The orbit center is placed on the viewing ray, at the depth of the scene center when it is in front of the camera.
     */
    function matchOrbitToView(view)
    {
        const cameraToWorld = view.inverted()
        const position = cameraToWorld.times(Qt.vector3d(0, 0, 0))
        const direction = cameraToWorld.times(Qt.vector3d(0, 0, -1)).minus(position).normalized()

        const bounds = sceneView.boundingBox
        const sceneDepth = bounds.valid ? bounds.center.minus(position).dotProduct(direction) : 0
        const distance = sceneDepth > 1e-3 ? sceneDepth : (bounds.valid && bounds.maxExtent > 0 ? bounds.maxExtent : 1.0)

        // setCenter() keeps the camera position: look at the target position, then move the camera onto it
        // (skipped when already there, as looking at the camera position itself is undefined)
        if (sceneView.cameraPosition().minus(position).length() > 1e-6)
        {
            fallbackMotionInfo.setCenter(position)
            fallbackMotionInfo.setDistance(0)
        }
        // Then look along the viewing direction, with the orbit center at the chosen distance
        fallbackMotionInfo.setCenter(position.plus(direction.times(distance)))
    }

    function restoreFallbackSceneState()
    {
        // Leaving an SfM camera: keep its viewpoint
        const leftView = sceneView.motionInfo === sfmMotionInfo ? sfmMotionInfo.pose : null

        imageLayer.visible = false
        imageLayer.source = ""
        sceneView.motionInfo = fallbackMotionInfo
        sceneView.cameraInfo = fallbackCameraInfo

        if (leftView)
        {
            matchOrbitToView(leftView)
        }
    }

    /** Look through the camera @p viewId of @p sfmDataObject and display its image. */
    function syncSfmSceneState(sfmDataObject, viewId)
    {
        if (!sfmDataObject.hasCameraTransform(viewId))
        {
            return
        }

        const sfmCameraInfo = sfmDataObject.getCameraInfo(viewId)
        if (!sfmCameraInfo)
        {
            return
        }

        sfmMotionInfo.pose = sfmDataObject.getCameraTransform(viewId)
        sceneView.motionInfo = sfmMotionInfo
        sceneView.cameraInfo = sfmCameraInfo

        imageLayer.setIntrinsics(sfmDataObject, viewId)
        imageLayer.source = sfmDataObject.getImagePath(viewId)
        imageLayer.visible = true
    }

    function syncViewPoint()
    {
        const sfmDataObject = collection.selectedSfmDataObject
        if (!sfmDataObject)
        {
            restoreFallbackSceneState()
            return
        }

        if (scene && isValidSelectedViewId(scene.selectedViewId))
        {
            syncSfmSceneState(sfmDataObject, scene.selectedViewId)
        }
    }

    /**
     * Return the name of the survey point receiving a 3d pick: the selected shape, or the last element
     * of the selected ShapeList while adding elements to it in the 2d Viewer (the element just added).
     * Return an empty string if there is none.
     */
    function pickingTargetShapeName()
    {
        if (!selectedShapeName || !ShapeViewerHelper.isListPlacement || !scene)
        {
            return selectedShapeName
        }

        const shapeList = scene.graph.attribute(selectedShapeName) || scene.graph.internalAttribute(selectedShapeName)
        if (!shapeList || shapeList.value.count === 0)
        {
            return ""
        }

        return shapeList.value.at(shapeList.value.count - 1).fullName
    }

    /** Store the point picked on mesh @p layer as the selected survey point's observation. */
    function handlePickingShape(layer)
    {
        const shapeName = pickingTargetShapeName()
        if (!shapeName)
        {
            return
        }

        SurveyPointViewerHelper.setPickedPosition(shapeName, layer.selection.x, -layer.selection.y, -layer.selection.z)
    }

    function moveToCameraCenter(layer)
    {
        const viewId = layer.selectedCamera
        if (!orbit || !layer.sfmData || !isValidCameraId(viewId) || !layer.sfmData.hasCameraTransform(viewId))
        {
            return
        }

        orbit.setCenter(layer.sfmData.getCameraCenter(viewId))
    }

    /** Dispatch a pick result: user code 0 selects (shape observation / camera), code 1 recenters the orbit. */
    function handlePickingLayerChanged()
    {
        const layer = sceneView.pickingLayer
        const select = sceneView.userCode == 0

        if (layer instanceof MeshLayer)
        {
            if (select)
            {
                handlePickingShape(layer)
            }
            else if (orbit)
            {
                orbit.setCenter(layer.selection)
            }
        }
        else if (layer instanceof SfmDataLayer)
        {
            if (select)
            {
                syncSelectedCameraToScene(layer)
            }
            else
            {
                moveToCameraCenter(layer)
            }
        }
    }

    /** Return the selected survey point's observation in the selected view, or null. */
    function getSelectedObservation()
    {
        if (!selectedShapeName || !scene)
        {
            return null
        }

        const shape = scene.graph.attribute(selectedShapeName) || scene.graph.internalAttribute(selectedShapeName)
        if (!shape || shape.type !== "SurveyPoint")
        {
            return null
        }

        return shape.geometry.getObservation(scene.selectedViewId) || null
    }

    SceneView {
        id: sceneView
        anchors.fill: parent

        property var imageLayerRef: imageLayer
        property var gridLayerRef: gridLayer
        property var axisLayerRef: axisLayer
        property var pointLayerRef: pointLayer
        property var boxControlLayerRef: boxControlLayer

        motionInfo: fallbackMotionInfo
        cameraInfo: fallbackCameraInfo

        OrbitMotionInfo {
            id: fallbackMotionInfo
        }

        AVMotionInfo {
            id: sfmMotionInfo
        }

        BaseCameraInfo {
            id: fallbackCameraInfo

            fov: 70.0
            nearPlane: 0.1
            farPlane: 10000
        }

        layers: [
            AxisLayer {
                id: axisLayer
            },
            GridLayer {
                id: gridLayer
            },
            ImageLayer {
                id: imageLayer
                visible: true
            },
            PointLayer {
                id: pointLayer
                visible: SurveyPointViewerHelper.hasSelectedNodeSurveyPoint
                positions: SurveyPointViewerHelper.positions
            },
            BoxControlLayer {
                id: boxControlLayer
                visible: false
            }
        ]

        FreeViewMouseArea {
            anchors.fill: parent
            enabled: collection.selectedSfmDataObject === null
            sceneView: sceneView
            zoomSpeed: collection.zoomSpeed
            focusTarget: root
        }

        SfmViewMouseArea {
            anchors.fill: parent
            enabled: collection.selectedSfmDataObject !== null
            sceneView: sceneView
            focusTarget: root
        }

        // Declared last to sit on top of the other mouse areas: presses outside the gizmo fall through to them
        BoxControlMouseArea {
            id: boxControlMouseArea
            anchors.fill: parent
            enabled: boxControlLayer.visible && collection.selectedSfmDataObject === null
            sceneView: sceneView
            boxLayer: boxControlLayer
            focusTarget: root

            onEditFinished: (type) => meshingBoundingBox.commit(type)
        }
    }

    SceneObjectCollection {
        id: collection
        sceneView: sceneView
    }

    MeshingBoundingBox {
        id: meshingBoundingBox
        node: collection.boundingBoxNode
        layer: boxControlLayer
        editing: boxControlMouseArea.dragging
        userVisible: collection.showBoundingBox
    }

    // Source: collection (SceneObjectCollection), whose selectedSfmDataObject tracks the currently
    // selected SfM dataset layer. Reason: when that selection changes, the viewpoint (camera pose,
    // motion info and background image) must be resynced to match the newly selected dataset.
    Connections {
        target: collection

        function onSelectedSfmDataObjectChanged()
        {
            syncViewPoint()
        }
    }

    // Source: sceneView (SceneView), whose pickingLayer/userCode report the result of a user pick in
    // the 3D view. Reason: dispatch that pick result to the right handler, either selecting a shape
    // observation/camera (userCode 0) or recentering the orbit on the picked point (userCode 1).
    Connections {
        target: sceneView

        function onPickingLayerChanged()
        {
            handlePickingLayerChanged()
        }
    }

    // Source: root.scene (the _currentScene context property), whose selectedViewId is driven by the
    // rest of the Meshroom UI (e.g. the image gallery). Reason: propagate that externally-driven
    // selection into the 3D view by updating every SfmDataLayer's selected camera and resyncing the
    // viewpoint accordingly.
    Connections {
        target: root.scene

        function onSelectedViewIdChanged()
        {
            // Convert the scene's "-1" string sentinel to SfmDataLayer's numeric UndefinedIndexT
            const viewId = root.scene.selectedViewId
            collection.setSelectedCameraForAll(isValidSelectedViewId(viewId) ? Number(viewId) : invalidCameraId)
            syncViewPoint()
        }
    }

    // Source: collection.boundingBoxNode, the node whose bounding box is edited in the viewer.
    // Reason: stop displaying the bounding box of a node removed from the graph.
    Connections {
        target: collection.boundingBoxNode

        function onAliveChanged()
        {
            if (!collection.boundingBoxNode.alive)
            {
                collection.boundingBoxNode = null
            }
        }
    }

    // Source: imageLayer (ImageLayer), whose errorString is set when its image fails to load.
    // Reason: the image layer is unique, so it is hidden rather than removed on failure.
    Connections {
        target: imageLayer

        function onErrorStringChanged()
        {
            if (imageLayer.errorString)
            {
                console.warn(`Viewer3D: failed to load image "${imageLayer.source}": ${imageLayer.errorString}`)
                imageLayer.visible = false
            }
        }
    }

    // Source: ShapeViewerHelper (singleton), whose selectedShapeNames reflects the survey point/shape
    // selected elsewhere in the UI (e.g. attribute editor). Reason: when that selection changes, center
    // the orbit on the corresponding picked observation so the selected point stays in view.
    Connections {
        target: ShapeViewerHelper

        function onSelectedShapeNamesChanged()
        {
            const obs = getSelectedObservation()
            if (obs && obs.picked3d && orbit)
            {
                orbit.setCenter(Qt.vector3d(obs.X, -obs.Y, -obs.Z))
            }
        }
    }

    /**
     * Add @p source to the LayerList matching its file extension (see layerListByExtension), under
     * the optional @p label. If @p source was read from @p attribute, the layer is removed when that
     * attribute or its node changes. Does nothing if the extension is not supported.
     * Returns true if the file was loaded, false if its extension is not supported.
     */
    function view(source, label = undefined, attribute = undefined)
    {
        const layerList = layerListByExtension[Filepath.extension(source)]
        if (!layerList)
        {
            return false
        }

        layerList.add(source, label, attribute)
        
        return true
    }

    /**
     * View the file referenced by a computed node's File @p attribute, if any.
     * If the node has an editable bounding box (e.g. Meshing), also display it, even if the node is not computed.
     * Used when dropping/selecting a node output attribute onto the 3D viewer.
     * Returns true if the attribute or the bounding box was actually viewed, false otherwise.
     */
    function viewAttribute(attribute)
    {
        let viewed = false
        if (attribute.node.hasAttribute("useBoundingBox"))
        {
            collection.boundingBoxNode = attribute.node
            viewed = true
        }

        if (attribute.desc.type === "File" && attribute.node.isComputed)
        {
            const source = resolveViewTemplate(attribute.value)
            if (source)
            {
                const layerList = layerListByExtension[Filepath.extension(source)]
                viewed = view(source, `${attribute.node.label}.${attribute.label}`, attribute) || viewed
                // A templated attribute shows one view at a time: drop the mesh of the previous view
                if (layerList && source !== attribute.value)
                {
                    layerList.removeAttributeSourcesLater(attribute, source)
                }
            }
        }

        return viewed
    }

    /**
     * Resolve the view placeholders (<VIEW_ID>, <FILENAME>, ...) of @p path with the view picked in
     * the 2D viewer, as Viewer2D does.
     * Returns @p path unchanged if it has no placeholder, and "" if it has one but no view is picked
     * or the resolved file does not exist.
     */
    function resolveViewTemplate(path)
    {
        if (!/<\w+>/.test(path))
        {
            return path
        }

        if (!root.scene || !root.scene.viewpoints)
        {
            return ""
        }

        for (let i = 0; i < root.scene.viewpoints.count; i++)
        {
            const vp = root.scene.viewpoints.at(i)
            if (vp.childAttribute("viewId").value == root.scene.pickedViewId)
            {
                const resolved = Filepath.resolve(path, vp)
                return Filepath.exists(resolved) ? resolved : ""
            }
        }

        return ""
    }
}
