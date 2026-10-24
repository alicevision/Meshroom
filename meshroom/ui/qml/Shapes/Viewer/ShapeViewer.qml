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

    // Update ShapeViewerHelper
    // This is usefull for new observation initialization
    onContainerWidthChanged: { ShapeViewerHelper.containerWidth = shapeViewer.containerWidth }
    onContainerHeightChanged: { ShapeViewerHelper.containerHeight = shapeViewer.containerHeight }
    onContainerScaleChanged: { ShapeViewerHelper.containerScale = shapeViewer.containerScale }

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

    // Reset selection
    TapHandler {
        enabled: !ShapeViewerHelper.isPlacing
        acceptedButtons: Qt.LeftButton
        gesturePolicy: TapHandler.WithinBounds
        onTapped: { ShapeViewerHelper.clearSelection() }
    }

    // Shape placement: left click adds the selected shape observation, right click cancels
    // Note: declared last to be above the shape layers
    MouseArea {
        anchors.fill: parent
        enabled: ShapeViewerHelper.isPlacing
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        cursorShape: Qt.CrossCursor
        onPressed: function(mouse) {
            // Let Shift+Left reach Viewer2D for panning
            if (mouse.button === Qt.LeftButton && (mouse.modifiers & Qt.ShiftModifier))
                mouse.accepted = false
        }
        onClicked: function(mouse) {
            if (mouse.button === Qt.RightButton) {
                ShapeViewerHelper.cancelPlacement()
                return
            }
            // Visible viewport expressed in image coordinates (handles zoom and EXIF rotation)
            const visible = viewport ? shapeViewer.mapFromItem(viewport, 0, 0, viewport.width, viewport.height)
                                     : Qt.rect(0, 0, containerWidth, containerHeight)
            ShapeViewerHelper.placeSelectedShapeAt(mouse.x, mouse.y, visible.width, visible.height)
        }
    }
}