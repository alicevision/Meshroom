import QtQuick
import QtQuick.Controls

import meshViewer

/**
 * Mouse interactions with the gizmo of a BoxControlLayer @p boxLayer displayed in @p sceneView:
 * hovering highlights a handle, left drag on a handle translates / rotates / scales the box or moves one
 * of its faces, right click on a handle opens a reset menu.
 * Presses outside the handles, or with Alt / Ctrl, are left to the mouse areas below (camera, picking).
 *
 * The layer is modified live while dragging; editFinished(type) is emitted once the edit is done,
 * with type in "translation", "rotation", "scale" or "all".
 */
MouseArea {
    id: root

    property var sceneView: null
    property BoxControlLayer boxLayer: null
    property Item focusTarget: null
    /** Smallest half extent the box can be scaled down to. */
    property real minimumScale: 0.001

    /** Handle being dragged, or BoxControlLayer.NoHandle. */
    property int activeHandle: BoxControlLayer.NoHandle
    readonly property bool dragging: activeHandle !== BoxControlLayer.NoHandle

    // Drag state captured on press
    property vector3d initialTranslation
    property vector3d initialRotation
    property vector3d initialScale
    property vector2d pressPosition
    property vector2d screenCenter
    /** World direction of the dragged handle axis. */
    property vector3d axisDirection
    /** Normalized screen direction of the dragged handle axis. */
    property vector2d screenAxis
    /** Screen length (pixels) of one world unit along the dragged handle axis. */
    property real pixelsPerUnit: 0
    /** +1 when the dragged rotation axis points towards the camera, -1 otherwise. */
    property real rotationOrientation: 1

    signal editFinished(string type)

    hoverEnabled: true
    acceptedButtons: Qt.LeftButton | Qt.RightButton

    function setHighlight(handle)
    {
        if (boxLayer)
        {
            boxLayer.highlightedHandle = handle
        }
    }

    function handleUnder(mouse)
    {
        if (!boxLayer || (mouse.modifiers & (Qt.AltModifier | Qt.ControlModifier)))
        {
            return BoxControlLayer.NoHandle
        }

        return boxLayer.handleAt(sceneView, Qt.vector2d(mouse.x, mouse.y))
    }

    /** Return @p v with its component @p axis (0 = x, 1 = y, 2 = z) replaced by @p value. */
    function withComponent(v, axis, value)
    {
        return Qt.vector3d(axis === 0 ? value : v.x, axis === 1 ? value : v.y, axis === 2 ? value : v.z)
    }

    function component(v, axis)
    {
        return axis === 0 ? v.x : (axis === 1 ? v.y : v.z)
    }

    /** Edit type reported by editFinished() for @p handle. */
    function editType(handle)
    {
        if (boxLayer.isTranslateHandle(handle))
        {
            return "translation"
        }
        if (boxLayer.isRotateHandle(handle))
        {
            return "rotation"
        }
        if (boxLayer.isScaleHandle(handle))
        {
            return "scale"
        }
        return "all"
    }

    function startDrag(handle, mouse)
    {
        const axis = boxLayer.handleAxis(handle)
        const worldScale = boxLayer.gizmoWorldScale(sceneView)

        initialTranslation = boxLayer.translation
        initialRotation = boxLayer.rotation
        initialScale = boxLayer.scale
        pressPosition = Qt.vector2d(mouse.x, mouse.y)
        axisDirection = boxLayer.axisDirection(axis)

        // Project the handle axis on screen to convert mouse motion into world units along it
        screenCenter = sceneView.worldToScreen(initialTranslation)
        const axisEnd = sceneView.worldToScreen(initialTranslation.plus(axisDirection.times(worldScale)))
        const screenVector = axisEnd.minus(screenCenter)
        pixelsPerUnit = screenVector.length() / worldScale
        screenAxis = screenVector.normalized()

        const toCamera = sceneView.cameraPosition().minus(initialTranslation)
        rotationOrientation = axisDirection.dotProduct(toCamera) > 0 ? 1 : -1

        activeHandle = handle
        setHighlight(handle)
    }

    function updateDrag(mouse)
    {
        const axis = boxLayer.handleAxis(activeHandle)
        const mousePosition = Qt.vector2d(mouse.x, mouse.y)

        if (boxLayer.isRotateHandle(activeHandle))
        {
            // Signed screen angle swept around the gizmo center (y axis points down)
            const v0 = pressPosition.minus(screenCenter)
            const v1 = mousePosition.minus(screenCenter)
            const screenAngle = Math.atan2(v0.x * v1.y - v0.y * v1.x, v0.x * v1.x + v0.y * v1.y) * 180 / Math.PI
            // A clockwise screen motion is a negative rotation around an axis pointing towards the camera
            const angle = -screenAngle * rotationOrientation
            const localAxis = withComponent(Qt.vector3d(0, 0, 0), axis, 1)
            boxLayer.rotation = Transformations3DHelper.rotateEulerLocal(initialRotation, localAxis, angle)
            return
        }

        if (pixelsPerUnit <= 0)
        {
            return
        }

        // Mouse motion projected on the screen axis, in world units
        const offset = mousePosition.minus(pressPosition).dotProduct(screenAxis) / pixelsPerUnit
        const initialHalfExtent = component(initialScale, axis)

        if (boxLayer.isTranslateHandle(activeHandle))
        {
            boxLayer.translation = initialTranslation.plus(axisDirection.times(offset))
        }
        else if (boxLayer.isScaleHandle(activeHandle))
        {
            boxLayer.scale = withComponent(initialScale, axis, Math.max(minimumScale, initialHalfExtent + offset))
        }
        else if (boxLayer.isFaceHandle(activeHandle))
        {
            // Move the dragged face only: grow by half the offset and shift the center by the other half
            const sign = boxLayer.handleSign(activeHandle)
            const halfExtent = Math.max(minimumScale, initialHalfExtent + sign * offset / 2)
            const effectiveOffset = sign * (halfExtent - initialHalfExtent) * 2
            boxLayer.scale = withComponent(initialScale, axis, halfExtent)
            boxLayer.translation = initialTranslation.plus(axisDirection.times(effectiveOffset / 2))
        }
    }

    onExited: {
        if (!dragging)
        {
            setHighlight(BoxControlLayer.NoHandle)
        }
    }

    onPressed: (mouse) => {
        const handle = handleUnder(mouse)
        if (handle === BoxControlLayer.NoHandle)
        {
            // Let the mouse areas below handle the press
            mouse.accepted = false
            return
        }

        if (focusTarget)
        {
            focusTarget.forceActiveFocus()
        }

        if (mouse.button === Qt.RightButton)
        {
            resetMenu.popup()
            return
        }

        startDrag(handle, mouse)
    }

    onPositionChanged: (mouse) => {
        if (dragging)
        {
            updateDrag(mouse)
        }
        else if (mouse.buttons === Qt.NoButton)
        {
            setHighlight(handleUnder(mouse))
        }
    }

    onReleased: (mouse) => {
        if (!dragging || mouse.button !== Qt.LeftButton)
        {
            return
        }

        // Report the edit before releasing the handle, so that the new values are committed
        // before anything bound to "dragging" re-applies the previous ones
        editFinished(editType(activeHandle))
        activeHandle = BoxControlLayer.NoHandle
        setHighlight(handleUnder(mouse))
    }

    onCanceled: {
        if (dragging)
        {
            editFinished(editType(activeHandle))
            activeHandle = BoxControlLayer.NoHandle
        }
    }

    Menu {
        id: resetMenu

        MenuItem {
            text: "Reset Translation"
            onTriggered: {
                root.boxLayer.translation = Qt.vector3d(0, 0, 0)
                root.editFinished("translation")
            }
        }
        MenuItem {
            text: "Reset Rotation"
            onTriggered: {
                root.boxLayer.rotation = Qt.vector3d(0, 0, 0)
                root.editFinished("rotation")
            }
        }
        MenuItem {
            text: "Reset Scale"
            onTriggered: {
                root.boxLayer.scale = Qt.vector3d(1, 1, 1)
                root.editFinished("scale")
            }
        }
        MenuItem {
            text: "Reset All"
            onTriggered: {
                root.boxLayer.translation = Qt.vector3d(0, 0, 0)
                root.boxLayer.rotation = Qt.vector3d(0, 0, 0)
                root.boxLayer.scale = Qt.vector3d(1, 1, 1)
                root.editFinished("all")
            }
        }
        MenuItem {
            text: "Gizmo Size"
            Slider {
                anchors.right: parent.right
                anchors.rightMargin: 10
                height: parent.height
                width: parent.width * 0.40

                from: 0.06
                to: 0.30
                stepSize: 0.01
                value: root.boxLayer ? root.boxLayer.gizmoSize : 0.15
                onMoved: root.boxLayer.gizmoSize = value
            }
        }
    }
}
