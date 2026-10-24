import QtQuick
import QtQuick.Shapes

import "Utils" as LayerUtils

/**
* RectangleLayer
*
* @biref Allows to display and modify a rectangle.
* @param name - the given shape name
* @param properties - the given shape style properties
* @param observation - the given shape position and dimensions for the current view
* @param editable - the shape is editable
* @param scaleRatio - the shape container scale ratio (scroll zoom)
* @param selected - the shape is selected
* @see BaseLayer.qml
*/
BaseLayer {
    id: rectangleLayer
    moveTarget: draggableRectangle

    // Rectangle edges from the observation, updated while a corner handle is dragged
    property real rectangleLeft: (rectangleLayer.observation.center.x - rectangleLayer.observation.size.width * 0.5) || 0
    property real rectangleRight: (rectangleLayer.observation.center.x + rectangleLayer.observation.size.width * 0.5) || 0
    property real rectangleTop: (rectangleLayer.observation.center.y - rectangleLayer.observation.size.height * 0.5) || 0
    property real rectangleBottom: (rectangleLayer.observation.center.y + rectangleLayer.observation.size.height * 0.5) || 0

    // Rectangle size from its edges (a corner can be dragged past the opposite one)
    property real rectangleWidth: Math.max(1.0, Math.abs(rectangleRight - rectangleLeft))
    property real rectangleHeight: Math.max(1.0, Math.abs(rectangleBottom - rectangleTop))

    // Commit the move of the rectangle (and of the other selected shapes)
    function commitMove() {
        if (commitSelectionMove())
            return
        _currentScene.setObservationFromName(name, _currentScene.selectedViewId, {
            center: {
                x: handleCenter.x + draggableRectangle.x,
                y: handleCenter.y + draggableRectangle.y
            }
        })
    }

    // Commit the resize of the rectangle from its edges
    function commitResize() {
        _currentScene.setObservationFromName(name, _currentScene.selectedViewId, {
            center: {
                x: (rectangleLeft + rectangleRight) * 0.5,
                y: (rectangleTop + rectangleBottom) * 0.5
            },
            size: {
                width: rectangleWidth,
                height: rectangleHeight
            }
        })
    }

    // Rectangle shape
    Shape {
        id : draggableRectangle

        // Rectangle path 
        ShapePath {
            fillColor: rectangleLayer.properties.fillColor || "transparent"
            strokeColor: rectangleLayer.properties.strokeColor || rectangleLayer.properties.color || rectangleLayer.defaultColor
            strokeWidth: getScaledStrokeWidth()

            PathRectangle {
                x: Math.min(rectangleLayer.rectangleLeft, rectangleLayer.rectangleRight)
                y: Math.min(rectangleLayer.rectangleTop, rectangleLayer.rectangleBottom)
                width: rectangleWidth
                height: rectangleHeight
            }
        }

        // Selection and move area
        LayerUtils.MoveArea {
            x: Math.min(rectangleLayer.rectangleLeft, rectangleLayer.rectangleRight)
            y: Math.min(rectangleLayer.rectangleTop, rectangleLayer.rectangleBottom)
            width: rectangleWidth
            height: rectangleHeight
            shapeLayer: rectangleLayer
            onMoved: rectangleLayer.commitMove()
        }

        // Handle for rectangle center
        LayerUtils.Handle {
            id: handleCenter
            x: (rectangleLayer.rectangleLeft + rectangleLayer.rectangleRight) * 0.5
            y: (rectangleLayer.rectangleTop + rectangleLayer.rectangleBottom) * 0.5
            size: getScaledHandleSize()
            scaleRatio: rectangleLayer.scaleRatio
            target: draggableRectangle
            cursorShape: Qt.SizeAllCursor
            visible: rectangleLayer.editable && rectangleLayer.selected
            onTapped: function(modifiers) { selectionRequested(modifiers) }
            onMoved: rectangleLayer.commitMove()
        }

        // Corner handles: drag a corner to resize the rectangle, the opposite corner stays in place
        // Note: the dragged handle updates the edges, which the other handles follow
        LayerUtils.Handle {
            id: handleTopLeft
            x: rectangleLayer.rectangleLeft
            y: rectangleLayer.rectangleTop
            size: getScaledHandleSize()
            scaleRatio: rectangleLayer.scaleRatio
            cursorShape: Qt.SizeFDiagCursor
            visible: rectangleLayer.editable && rectangleLayer.selected
            onXChanged: { if (active) rectangleLayer.rectangleLeft = x }
            onYChanged: { if (active) rectangleLayer.rectangleTop = y }
            onMoved: rectangleLayer.commitResize()
        }

        LayerUtils.Handle {
            id: handleTopRight
            x: rectangleLayer.rectangleRight
            y: rectangleLayer.rectangleTop
            size: getScaledHandleSize()
            scaleRatio: rectangleLayer.scaleRatio
            cursorShape: Qt.SizeBDiagCursor
            visible: rectangleLayer.editable && rectangleLayer.selected
            onXChanged: { if (active) rectangleLayer.rectangleRight = x }
            onYChanged: { if (active) rectangleLayer.rectangleTop = y }
            onMoved: rectangleLayer.commitResize()
        }

        LayerUtils.Handle {
            id: handleBottomLeft
            x: rectangleLayer.rectangleLeft
            y: rectangleLayer.rectangleBottom
            size: getScaledHandleSize()
            scaleRatio: rectangleLayer.scaleRatio
            cursorShape: Qt.SizeBDiagCursor
            visible: rectangleLayer.editable && rectangleLayer.selected
            onXChanged: { if (active) rectangleLayer.rectangleLeft = x }
            onYChanged: { if (active) rectangleLayer.rectangleBottom = y }
            onMoved: rectangleLayer.commitResize()
        }

        LayerUtils.Handle {
            id: handleBottomRight
            x: rectangleLayer.rectangleRight
            y: rectangleLayer.rectangleBottom
            size: getScaledHandleSize()
            scaleRatio: rectangleLayer.scaleRatio
            cursorShape: Qt.SizeFDiagCursor
            visible: rectangleLayer.editable && rectangleLayer.selected
            onXChanged: { if (active) rectangleLayer.rectangleRight = x }
            onYChanged: { if (active) rectangleLayer.rectangleBottom = y }
            onMoved: rectangleLayer.commitResize()
        }
    }
}