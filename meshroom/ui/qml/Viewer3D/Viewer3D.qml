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

    function restoreFallbackSceneState()
    {
        imageLayer.visible = false
        imageLayer.source = ""
        sceneView.motionInfo = fallbackMotionInfo
        sceneView.cameraInfo = fallbackCameraInfo
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

    /** Store the point picked on mesh @p layer as the selected survey point's observation. */
    function handlePickingShape(layer)
    {
        if (!scene)
        {
            return
        }

        const selectedShapeName = ShapeViewerHelper.selectedShapeName
        if (!selectedShapeName)
        {
            return
        }

        const observationKey = SurveyPointViewerHelper.observationKeyForSelectedSurveyPoint(selectedShapeName)
        if (!observationKey)
        {
            return
        }

        scene.setObservationFromName(selectedShapeName, observationKey, {
            "X": layer.selection.x,
            "Y": -layer.selection.y,
            "Z": -layer.selection.z,
            "picked": true
        })
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
        const selectedShapeName = ShapeViewerHelper.selectedShapeName
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
            },
            GridLayer {
                id: gridLayer
            },
            ImageLayer {
                id: imageLayer
                visible: true
            },
            SphereLayer {
                id: sphereLayer
                visible: SurveyPointViewerHelper.hasSelectedNodeSurveyPoint
                positions: SurveyPointViewerHelper.positions
            }
        ]

        FreeViewMouseArea {
            anchors.fill: parent
            enabled: collection.selectedSfmDataObject === null
            sceneView: sceneView
            focusTarget: root
        }

        SfmViewMouseArea {
            anchors.fill: parent
            enabled: collection.selectedSfmDataObject !== null
            sceneView: sceneView
            focusTarget: root
        }
    }

    SceneObjectCollection {
        id: collection
        sceneView: sceneView
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

    // Source: ShapeViewerHelper (singleton), whose selectedShapeName reflects the survey point/shape
    // selected elsewhere in the UI (e.g. attribute editor). Reason: when that selection changes, center
    // the orbit on the corresponding picked observation so the selected point stays in view.
    Connections {
        target: ShapeViewerHelper

        function onSelectedShapeNameChanged()
        {
            const obs = getSelectedObservation()
            if (obs && obs.picked && orbit)
            {
                orbit.setCenter(Qt.vector3d(obs.X, -obs.Y, -obs.Z))
            }
        }
    }

    /**
     * Add @p source to the LayerList matching its file extension (see layerListByExtension), under
     * the optional @p label. Does nothing if the extension is not supported.
     * Returns true (even if the extension was unsupported) so callers can treat this as "handled".
     */
    function view(source, label = undefined)
    {
        const layerList = layerListByExtension[Filepath.extension(source)]
        if (layerList)
        {
            layerList.add(source, label)
        }

        return true
    }

    /**
     * View the file referenced by a computed node's File @p attribute, if any.
     * Used when dropping/selecting a node output attribute onto the 3D viewer.
     * Returns true if the attribute was actually viewed, false otherwise.
     */
    function viewAttribute(attribute)
    {
        if (attribute.desc.type === "File" && attribute.node.isComputed)
        {
            return view(attribute.value, `${attribute.node.label}.${attribute.label}`)
        }

        return false
    }
}
