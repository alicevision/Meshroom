import QtQuick

/**
 * Interactions while looking through an SfM camera on @p sceneView:
 * Shift + left drag to pan, Shift + wheel to zoom the camera image plane.
 */
DragMouseArea {
    id: root

    property var sceneView: null
    readonly property var cameraInfo: sceneView ? sceneView.cameraInfo : null

    property real initialPanX: 0
    property real initialPanY: 0

    function clampUnit(value) {
        return Math.max(-1.0, Math.min(1.0, value))
    }

    onPressed: {
        initialPanX = cameraInfo.panX
        initialPanY = cameraInfo.panY
    }

    onPositionChanged: (mouse) => {
        if (draggingLeft && (mouse.modifiers & Qt.ShiftModifier))
        {
            cameraInfo.panX = clampUnit(initialPanX + (mouse.x - initialX) * 0.002)
            cameraInfo.panY = clampUnit(initialPanY - (mouse.y - initialY) * 0.002)
        }
    }

    onWheel: function(wheel) {
        if (wheel.modifiers & Qt.ShiftModifier)
        {
            cameraInfo.zoom = Math.max(0.1, cameraInfo.zoom + wheel.angleDelta.y * 0.001)
            wheel.accepted = true
        }
    }
}
