import QtQuick

/**
 * Free camera interactions on @p sceneView:
 * Alt + left/middle/right drag to rotate/pan/zoom, Alt + wheel to zoom,
 * Ctrl + click to pick (Ctrl + Shift + click to pick with user code 1).
 */
DragMouseArea {
    id: root

    property var sceneView: null
    readonly property var motionInfo: sceneView ? sceneView.motionInfo : null

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
            motionInfo.distance = deltaY * 0.05
        }
    }

    onWheel: function(wheel) {
        if ((wheel.modifiers & Qt.AltModifier) && !dragging)
        {
            // Qt reports the vertical wheel on the x axis while Alt is pressed
            motionInfo.distance = -wheel.angleDelta.x * 0.05
            motionInfo.applyTransform()
            wheel.accepted = true
        }
    }
}
