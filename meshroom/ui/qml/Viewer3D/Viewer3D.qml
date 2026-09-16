import meshViewer

import QtQuick
import QtQuick.Controls
import Utils 1.0

Item {
    
    id: root
    property alias collection: collection

    function isValidSelectedViewId(viewId)
    {
        if (viewId === undefined || viewId === null)
        {
            return false
        }

        const normalizedViewId = String(viewId)
        return normalizedViewId.length > 0 && normalizedViewId !== "-1"
    }

    // Sentinel used by SfmDataLayer.selectedCamera to mean "no camera selected" (UndefinedIndexT).
    // Declared as "var" (not "int") since QML's int is 32-bit signed and would overflow 0xFFFFFFFF to -1.
    readonly property var invalidCameraId: 0xFFFFFFFF

    function isValidCameraId(cameraId)
    {
        return cameraId !== undefined && cameraId !== null && cameraId !== invalidCameraId
    }

    function syncSelectedCameraToScene(layer)
    {
        if (typeof _currentScene === "undefined" || !_currentScene)
        {
            return
        }

        const cameraId = layer.selectedCamera
        if (!isValidCameraId(cameraId))
        {
            return
        }

        _currentScene.selectedViewId = String(cameraId)
    }

    function restoreFallbackSceneState()
    {
        sceneView.imageLayerRef.visible = false
        sceneView.imageLayerRef.source = ""
        sceneView.motionInfo = fallbackMotionInfo
        sceneView.cameraInfo = fallbackCameraInfo
    }

    function syncSfmSceneState(sfmDataObject, viewId)
    {
        const pose = sfmDataObject.getCameraTransform(viewId)

        sfmMotionInfo.pose = pose
        sceneView.motionInfo = sfmMotionInfo

        if (sceneView.imageLayerRef)
        {
            sceneView.imageLayerRef.source = sfmDataObject.getImagePath(viewId)
            sceneView.imageLayerRef.visible = true
        }

        const sfmCameraInfo = sfmDataObject.getCameraInfo(viewId)
        if (sfmCameraInfo)
        {
            sceneView.cameraInfo = sfmCameraInfo
        }
    }

    function syncViewPoint()
    {
        const sfmDataObject = collection.selectedSfmDataObject
        const viewId = _currentScene.selectedViewId
        
        if (!sfmDataObject)
        {
            restoreFallbackSceneState()
            return
        }

        if (!isValidSelectedViewId(viewId))
        {
            return
        }

        if (!sfmDataObject.hasCameraTransform(viewId))
        {
            return
        }

        syncSfmSceneState(sfmDataObject, viewId)
    }

    function handlePickingShape(layer) {

        if (typeof _currentScene === "undefined" || !_currentScene) {
            return
        }

        const selectedShapeName = ShapeViewerHelper.selectedShapeName
        if (!selectedShapeName) {
            return
        }

        const observationKey = SurveyPointViewerHelper.observationKeyForSelectedSurveyPoint(selectedShapeName)
        if (!observationKey) {
            return
        }

        _currentScene.setObservationFromName(selectedShapeName, observationKey, {
            "X": layer.selection.x,
            "Y": -layer.selection.y,
            "Z": -layer.selection.z,
            "picked": true
        })
    }

    function moveToCameraCenter(layer)
    {
        if (layer.sfmData == null)
        {
            return
        }

        var viewId = layer.selectedCamera

        if (!isValidSelectedViewId(viewId))
        {
            return
        }

        if (!layer.sfmData.hasCameraTransform(viewId))
        {
            return
        }

        if (sceneView.motionInfo instanceof OrbitMotionInfo)
        {
            sceneView.motionInfo.setCenter(layer.sfmData.getCameraCenter(viewId))
        }
    }

    function handlePickingLayerChanged()
    {
        const layer = sceneView.pickingLayer
        const code = sceneView.userCode

        if (!layer)
        {
            return
        }

        if (layer instanceof MeshLayer)
        {
            if (code == 0)
            {
                handlePickingShape(layer)
            }
            else 
            {
                if (sceneView.motionInfo instanceof OrbitMotionInfo)
                {
                    sceneView.motionInfo.setCenter(layer.selection)
                }
            }
        }
        else if (layer instanceof SfmDataLayer)
        {
            if (code == 0)
            {
                syncSelectedCameraToScene(layer)
            }
            else 
            {
                moveToCameraCenter(layer)
            }
        }
    }

    SceneView {
        id: sceneView
        anchors.fill: parent
        focus: true
        
        property var imageLayerRef: null
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
            ImageLayer{
                id: imageLayer
                visible: true
                Component.onCompleted: sceneView.imageLayerRef = imageLayer
            },
            SphereLayer {
                id: sphereLayer
                visible: SurveyPointViewerHelper.hasSelectedNodeSurveyPoint
                positions: SurveyPointViewerHelper.positions
            }
        ]

        MouseArea {
            id: freeViewMouseArea
            anchors.fill: parent
            acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
            enabled: collection.selectedSfmDataObject === null

            property real initialX: 0
            property real initialY: 0
            property bool draggingLeft: false
            property bool draggingMiddle: false
            property bool draggingRight: false

            onClicked: (mouse) => {

                if (mouse.button === Qt.LeftButton && (mouse.modifiers & Qt.ControlModifier))
                {
                    var code = 0;
                    if (mouse.modifiers & Qt.ShiftModifier)
                    {
                        code = 1;
                    }

                    sceneView.pick(Qt.vector2d(mouse.x, mouse.y), code)
                }
            }

            onPressed: (mouse) => {
                initialX = mouse.x
                initialY = mouse.y
                draggingLeft = (mouse.button === Qt.LeftButton)
                draggingMiddle = (mouse.button === Qt.MiddleButton)
                draggingRight = (mouse.button === Qt.RightButton)
            }

            onReleased: (mouse) => {
                if (mouse.button === Qt.RightButton)
                {
                    draggingRight = false
                }
                else if (mouse.button === Qt.LeftButton)
                {
                    draggingLeft = false
                }
                else if (mouse.button === Qt.MiddleButton)
                {
                    draggingMiddle = false
                }

                if (mouse.modifiers & Qt.AltModifier)
                {
                    sceneView.motionInfo.applyTransform()
                }
            }

            onPositionChanged: (mouse) => {
                const deltaX = mouse.x - initialX
                const deltaY = mouse.y - initialY

                if (draggingLeft)
                {
                    if (mouse.modifiers & Qt.AltModifier)
                    {
                        sceneView.motionInfo.relativeRotationX = deltaY * 0.5
                        sceneView.motionInfo.relativeRotationY = deltaX * 0.5
                    }
                }
                else if (draggingMiddle && (mouse.modifiers & Qt.AltModifier))
                {
                    sceneView.motionInfo.planeX = deltaX * 0.01
                    sceneView.motionInfo.planeY = deltaY * 0.01
                }
                else if (draggingRight && (mouse.modifiers & Qt.AltModifier))
                {
                   sceneView.motionInfo.distance = deltaY * 0.05;
                }
            }

            onWheel: function(wheel) {


                if (wheel.modifiers & Qt.AltModifier)
                {
                    if (!(draggingLeft || draggingMiddle || draggingRight))
                    {
                        const zoomStep = -wheel.angleDelta.x * 0.01
                        sceneView.motionInfo.distance = zoomStep
                        sceneView.motionInfo.applyTransform()
                        wheel.accepted = true
                    }
                }
            }
        }

        MouseArea {
            id: sfmViewMouseArea
            anchors.fill: parent
            acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
            enabled: collection.selectedSfmDataObject !== null
            
            property bool draggingLeft: false
            property bool draggingMiddle: false
            property bool draggingRight: false
            property real initialPanX: 0
            property real initialPanY: 0
            property real initialX: 0
            property real initialY: 0

            onPressed: (mouse) => {
                initialX = mouse.x
                initialY = mouse.y
                initialPanX = sceneView.cameraInfo.panX
                initialPanY = sceneView.cameraInfo.panY

                draggingLeft = (mouse.button === Qt.LeftButton)
                draggingMiddle = (mouse.button === Qt.MiddleButton)
                draggingRight = (mouse.button === Qt.RightButton)
            }

            onReleased: (mouse) => {
                if (mouse.button === Qt.RightButton)
                {
                    draggingRight = false
                }
                else if (mouse.button === Qt.LeftButton)
                {
                    draggingLeft = false
                }
                else if (mouse.button === Qt.MiddleButton)
                {
                    draggingMiddle = false
                }
            }

            onPositionChanged: (mouse) => {
                
                const deltaX = mouse.x - initialX
                const deltaY = mouse.y - initialY

                if (draggingLeft)
                {
                    if (mouse.modifiers & Qt.ShiftModifier)
                    {
                        sceneView.cameraInfo.panX = Math.max(-1.0, Math.min(1.0, initialPanX + deltaX * 0.002))
                        sceneView.cameraInfo.panY = Math.max(-1.0, Math.min(1.0, initialPanY - deltaY * 0.002))
                    }
                }
            }
            
            onWheel: function(wheel) {

                if (wheel.modifiers & Qt.ShiftModifier)
                {
                    const zoomStep = wheel.angleDelta.y * 0.001
                    sceneView.cameraInfo.zoom = Math.max(0.1, sceneView.cameraInfo.zoom + zoomStep)
                    wheel.accepted = true
                }
            }
        }
    }

    SceneObjectCollection {
        id: collection
        sceneView: sceneView
    }

    Connections {
        target: collection

        function onSelectedSfmDataObjectChanged()
        {
            syncViewPoint()
        }
    }

    Connections {
        target: sceneView

        function onPickingLayerChanged()
        {
            handlePickingLayerChanged()
        }
    }

    Connections {
        target: typeof _currentScene === "undefined" ? null : _currentScene

        function onSelectedViewIdChanged()
        {
            collection.setSelectedCameraForAll(_currentScene.selectedViewId)
            syncViewPoint()
        }
    }

    function getSelectedShape() {
        const selectedShapeName = ShapeViewerHelper.selectedShapeName
        if (!selectedShapeName || typeof _currentScene === "undefined" || !_currentScene) {
            return null
        }

        let shape = _currentScene.graph.attribute(selectedShapeName)
        if (!shape) {
            shape = _currentScene.graph.internalAttribute(selectedShapeName)
        }

        if (shape.type !== "SurveyPoint")
        {
            return null
        }

        let obs = shape.geometry.getObservation(_currentScene.selectedViewId)
        if (!obs)
        {
            return null
        }

        return obs
    }

    Connections {
        target: ShapeViewerHelper

        function onSelectedShapeNameChanged()
        {
            var obs = getSelectedShape()
            if (obs)
            {
                if (sceneView.motionInfo instanceof OrbitMotionInfo)
                {
                    var vec = Qt.vector3d(obs.X, -obs.Y, -obs.Z)
                    sceneView.motionInfo.setCenter(vec)
                }
            }
        }
    }

    function view(source, label = undefined) 
    {
        switch (Filepath.extension(source)) {
            case ".abc":
            case ".usda":
            case ".sfm":
            {
                collection.addSfmData(source, label)
                break
            }
            case ".obj":
            case ".glb":
            {
                collection.addMesh(source, label)
                break
            }
            case ".exr":
            {
                collection.addDepthmap(source, label)
            }
        }
            
        return true
    }

    function viewAttribute(attribute) {

        if (attribute.desc.type === "File")
        {
            var section = attribute.node.label

            view(attribute.value, `${section}.${attribute.label}`)
        }

        return false
    }
}