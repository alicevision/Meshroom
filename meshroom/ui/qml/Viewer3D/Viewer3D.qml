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

    SceneView {
        id: sceneView
        anchors.fill: parent
        focus: true
        
        property var imageLayerRef: null

        cameraInfo.fov: 70.0

        layers: [
            AxisLayer {
            },
            GridLayer {
                id: gridLayer
                minorFadeStartPixels: 1
                minorFadeEndPixels: 3
                minorOpacity: 0.45
                minorLineWidth: 1.1
            },
            ImageLayer{
                id: imageLayer
                Component.onCompleted: sceneView.imageLayerRef = imageLayer
            },
            SphereLayer {
                id: sphereLayer
                visible: Point3dViewerHelper.hasSelectedNodePoint3d
                positions: Point3dViewerHelper.positions
            }
        ]

        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton

            property real initialX: 0
            property real initialY: 0
            property real initialPanX: 0
            property real initialPanY: 0
            property bool draggingLeft: false
            property bool draggingMiddle: false
            property bool draggingRight: false

            onClicked: (mouse) => {
                if (mouse.button === Qt.LeftButton && (mouse.modifiers & Qt.CtrlModifier))
                {
                    sceneView.pick(Qt.vector2d(mouse.x, mouse.y))
                }
            }

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
                    else if (mouse.modifiers & Qt.ShiftModifier)
                    {
                        sceneView.cameraInfo.panX = Math.max(-1.0, Math.min(1.0, initialPanX + deltaX * 0.002))
                        sceneView.cameraInfo.panY = Math.max(-1.0, Math.min(1.0, initialPanY - deltaY * 0.002))
                    }
                }
                else if (draggingMiddle && (mouse.modifiers & Qt.AltModifier))
                {
                    sceneView.motionInfo.planeX = deltaX * 0.01
                    sceneView.motionInfo.planeY = deltaY * 0.01
                }
                else if (draggingRight && (mouse.modifiers & Qt.AltModifier))
                {
                   sceneView.motionInfo.distance = deltaY * 0.2;
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
        target: typeof _currentScene === "undefined" ? null : _currentScene

        function onSelectedViewIdChanged()
        {
            const viewId = _currentScene.selectedViewId
            if (!isValidSelectedViewId(viewId))
            {
                return
            }

            for (let i = 0; i < collection.sfmDataModel.count; ++i)
            {
                if (collection.sfmDataObjectAt(i).hasCameraTransform(viewId))
                {
                    const pose = collection.sfmDataObjectAt(i).getCameraTransform(viewId)
                    sceneView.setMotionTransform(pose)

                    var path = collection.sfmDataObjectAt(i).getImagePath(viewId)
                    sceneView.imageLayerRef.source = path

                    sceneView.cameraInfo = collection.sfmDataObjectAt(i).getCameraInfo(viewId)
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
            {
                collection.addMesh(source, label)
                break
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