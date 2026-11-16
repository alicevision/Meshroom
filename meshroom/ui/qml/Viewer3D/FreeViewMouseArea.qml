import QtQuick

import meshViewer

/**
 * Free camera interactions on @p sceneView:
 * Alt + left/middle/right drag to rotate/pan/zoom, Alt + wheel to zoom,
 * Ctrl + click to pick (Ctrl + Shift + click to pick with user code 1).
 * When the camera is orthographic, zooming changes its orthographicWidth (Maya-like)
 * instead of the orbit distance. @p zoomSpeed scales every zoom interaction.
 */
DragMouseArea {
    id: root

    property var sceneView: null
    readonly property var motionInfo: sceneView ? sceneView.motionInfo : null
    readonly property var cameraInfo: sceneView ? sceneView.cameraInfo : null
    /** Multiplier applied to zoom interactions (wheel and right drag). */
    property real zoomSpeed: 1.0
    /** True when the current camera is a BaseCameraInfo in orthographic mode. */
    readonly property bool isOrtho: cameraInfo instanceof BaseCameraInfo && cameraInfo.orthographic
    /** Orthographic width captured when the drag started. */
    property real initialOrthoWidth: 0

    onPressed: (mouse) => {
        if (isOrtho)
        {
            initialOrthoWidth = cameraInfo.orthographicWidth
        }
    }

    onClicked: (mouse) => {
        if (mouse.button === Qt.LeftButton && (mouse.modifiers & Qt.ControlModifier))
        {
            const code = (mouse.modifiers & Qt.ShiftModifier) ? 1 : 0
            sceneView.pick(Qt.vector2d(mouse.x, mouse.y), code)
        }
    }

    onReleased: (mouse) => {
        if (mouse.modifiers & Qt.AltModifier)
        {
            motionInfo.applyTransform()
        }
    }

    onPositionChanged: (mouse) => {
        if (!(mouse.modifiers & Qt.AltModifier))
        {
            return
        }

        const deltaX = mouse.x - initialX
        const deltaY = mouse.y - initialY

        if (draggingLeft)
        {
            motionInfo.relativeRotationX = deltaY * 0.5
            motionInfo.relativeRotationY = deltaX * 0.5
        }
        else if (draggingMiddle)
        {
            motionInfo.planeX = deltaX * 0.01
            motionInfo.planeY = deltaY * 0.01
        }
        else if (draggingRight)
        {
            if (isOrtho)
            {
                // Multiplicative zoom keeps the width positive
                cameraInfo.orthographicWidth = initialOrthoWidth * Math.exp(deltaY * 0.005 * zoomSpeed)
            }
            else
            {
                motionInfo.distance = deltaY * 0.05 * zoomSpeed
            }
        }
    }

    onWheel: function(wheel) {
        if ((wheel.modifiers & Qt.AltModifier) && !dragging)
        {
            // Qt reports the vertical wheel on the x axis while Alt is pressed
            if (isOrtho)
            {
                cameraInfo.orthographicWidth *= Math.exp(-wheel.angleDelta.x * 0.001 * zoomSpeed)
            }
            else
            {
                motionInfo.distance = -wheel.angleDelta.x * 0.05 * zoomSpeed
                motionInfo.applyTransform()
            }
            wheel.accepted = true
        }
    }
}
