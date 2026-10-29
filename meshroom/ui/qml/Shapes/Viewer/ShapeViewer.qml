import QtQuick

/**
* ShapeViewer
*
* @biref A canvas to display current node shape attributes and shape files.
* @param containerWidth  - the parent image container width
* @param containerHeight - the parent image container height
* @param containerScale  - the parent image container scale
* @param viewport        - the visible viewport item, used to size new observations
*/
Item {
    id: shapeViewer

    // Current node
    property var node: _currentScene ? _currentScene.selectedNode : null

    // Container dimensions and scale
    property real containerWidth: 0.0
    property real containerHeight: 0.0
    property real containerScale: 1.0

    // Visible viewport item
    property Item viewport: null

    // Container scale ratio
    property real scaleRatio: (1 / containerScale)

    // Emitted on a double click on empty space, in viewport coordinates (the 2d Viewer handles the zoom)
    signal emptyDoubleClicked(point position)

    // Update ShapeViewerHelper
    // This is usefull for new observation initialization
    onContainerWidthChanged: { ShapeViewerHelper.containerWidth = shapeViewer.containerWidth }
    onContainerHeightChanged: { ShapeViewerHelper.containerHeight = shapeViewer.containerHeight }
    onContainerScaleChanged: { ShapeViewerHelper.containerScale = shapeViewer.containerScale }

    // Selection area, declared first to be below the shape layers: it only receives presses on empty space
    // - click clears the selection (kept with Ctrl)
    // - left drag selects the shapes inside the rectangle, Ctrl+drag adds them to the selection
    // Note: Shift+Left (pan) is passed to the 2d Viewer, double click (zoom) is forwarded with emptyDoubleClicked
    MouseArea {
        id: selectionArea
        anchors.fill: parent
        enabled: !ShapeViewerHelper.isPlacing
        acceptedButtons: Qt.LeftButton
        property point pressPosition
        property bool additive: false

        onPressed: function(mouse) {
            if (mouse.modifiers & Qt.ShiftModifier) {
                mouse.accepted = false
                return
            }
            // Take the focus so that the 2d Viewer receives key events (e.g. Ctrl+A)
            shapeViewer.forceActiveFocus()
            pressPosition = Qt.point(mouse.x, mouse.y)
            additive = (mouse.modifiers & Qt.ControlModifier) !== 0
        }
        onPositionChanged: function(mouse) {
            // Drag threshold in screen pixels
            if (!selectionRect.visible && Math.max(Math.abs(mouse.x - pressPosition.x), Math.abs(mouse.y - pressPosition.y))
                                          * shapeViewer.containerScale < Qt.styleHints.startDragDistance)
                return
            selectionRect.x = Math.min(pressPosition.x, mouse.x)
            selectionRect.y = Math.min(pressPosition.y, mouse.y)
            selectionRect.width = Math.abs(mouse.x - pressPosition.x)
            selectionRect.height = Math.abs(mouse.y - pressPosition.y)
            selectionRect.visible = true
        }
        onReleased: {
            if (selectionRect.visible) {
                selectionRect.visible = false
                ShapeViewerHelper.selectShapesInRect(selectionRect.x, selectionRect.y,
                                                     selectionRect.width, selectionRect.height, additive)
            } else if (!additive) {
                ShapeViewerHelper.clearSelection()
            }
        }
        onCanceled: { selectionRect.visible = false }
        onDoubleClicked: function(mouse) {
            shapeViewer.emptyDoubleClicked(viewport ? selectionArea.mapToItem(viewport, mouse.x, mouse.y) : Qt.point(mouse.x, mouse.y))
        }
    }

    // Current node shape files
    // ShapeFilesHelper provide the model
    Repeater {
        model: ShapeFilesHelper.nodeShapeFiles
        delegate: Repeater {
            model: object.shapes
            delegate: ShapeViewerLayer {
                active: object.isVisible
                scaleRatio: shapeViewer.scaleRatio
                name: object.name
                type: object.type
                properties: object.properties
                observation: object.observation
                editable: false
            }
        }
    }
    
    // Current node shape attributes
    // Node attributes as the model
    Repeater {
        model: node.attributes
        delegate: ShapeViewerAttributeLoader {
            attribute: object
            scaleRatio: shapeViewer.scaleRatio
        }
    }

    Rectangle {
        id: selectionRect
        visible: false
        color: "#223399ff"
        border.color: "#bb3399ff"
        border.width: shapeViewer.scaleRatio
    }

    // Preview of the shape being defined by a drag in placement mode
    ShapeViewerLayer {
        id: dragPreview
        visible: placementArea.dragging
        type: ShapeViewerHelper.placementShapeType
        properties: ({})
        observation: null
        scaleRatio: shapeViewer.scaleRatio
    }

    // Shape placement, right click cancels (except in ShapeList multi-add mode, stopped from the 2d Viewer toolbar button)
    // - left click adds the selected shape observation with a default size
    // - left drag defines the shape geometry from the press to the release position
    // Note: declared last to be above the shape layers
    MouseArea {
        id: placementArea
        anchors.fill: parent
        enabled: ShapeViewerHelper.isPlacing
        acceptedButtons: ShapeViewerHelper.isListPlacement ? Qt.LeftButton : Qt.LeftButton | Qt.RightButton
        cursorShape: Qt.CrossCursor
        property point pressPosition
        property bool dragging: false

        onPressed: function(mouse) {
            // Let Shift+Left reach Viewer2D for panning
            if (mouse.button === Qt.LeftButton && (mouse.modifiers & Qt.ShiftModifier)) {
                mouse.accepted = false
                return
            }
            pressPosition = Qt.point(mouse.x, mouse.y)
            dragging = false
        }
        onPositionChanged: function(mouse) {
            if (!(mouse.buttons & Qt.LeftButton))
                return
            // Drag threshold in screen pixels
            if (!dragging && Math.max(Math.abs(mouse.x - pressPosition.x), Math.abs(mouse.y - pressPosition.y))
                             * shapeViewer.containerScale < Qt.styleHints.startDragDistance)
                return
            dragPreview.observation = ShapeViewerHelper.getPlacementDragObservation(pressPosition.x, pressPosition.y,
                                                                                    mouse.x, mouse.y)
            dragging = true
        }
        onReleased: function(mouse) {
            if (mouse.button === Qt.RightButton) {
                ShapeViewerHelper.cancelPlacement()
                return
            }
            // Visible viewport expressed in image coordinates (handles zoom and EXIF rotation)
            const visible = viewport ? shapeViewer.mapFromItem(viewport, 0, 0, viewport.width, viewport.height)
                                     : Qt.rect(0, 0, containerWidth, containerHeight)
            if (dragging) {
                dragging = false
                ShapeViewerHelper.placeSelectedShapeFromDrag(pressPosition.x, pressPosition.y, mouse.x, mouse.y,
                                                             visible.width, visible.height)
            } else {
                ShapeViewerHelper.placeSelectedShapeAt(mouse.x, mouse.y, visible.width, visible.height)
            }
        }
        onCanceled: { dragging = false }
    }
}