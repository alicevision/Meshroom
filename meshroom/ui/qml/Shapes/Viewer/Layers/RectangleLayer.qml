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

    // Rectangle width from handleWidth position
    property real rectangleWidth: Math.max(1.0, Math.abs(handleCenter.x- handleWidth.x) * 2)

    // Rectangle height from handleHeight position
    property real rectangleHeight: Math.max(1.0, Math.abs(handleCenter.y - handleHeight.y) * 2)

    // Commit the move of the rectangle
    function commitMove() {
        _currentScene.setObservationFromName(name, _currentScene.selectedViewId, {
            center: {
                x: handleCenter.x + draggableRectangle.x,
                y: handleCenter.y + draggableRectangle.y
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
                x: rectangleLayer.observation.center.x - (rectangleWidth * 0.5)
                y: rectangleLayer.observation.center.y - (rectangleHeight * 0.5)
                width: rectangleWidth
                height: rectangleHeight
            }
        }

        // Size helper path
        ShapePath {
            fillColor: "transparent"
            strokeColor: rectangleLayer.selected ? "#bbffffff" : "transparent"
            strokeWidth: getScaledHelperStrokeWidth()

            PathMove { x: rectangleLayer.observation.center.x; y: rectangleLayer.observation.center.y }
            PathLine { x: handleWidth.x; y: handleWidth.y }
            PathMove { x: rectangleLayer.observation.center.x; y: rectangleLayer.observation.center.y }
            PathLine { x: handleHeight.x; y: handleHeight.y }
        }

        // Selection and move area
        LayerUtils.MoveArea {
            x: handleCenter.x - rectangleWidth * 0.5
            y: handleCenter.y - rectangleHeight * 0.5
            width: rectangleWidth
            height: rectangleHeight
            shapeLayer: rectangleLayer
            onMoved: rectangleLayer.commitMove()
        }

        // Handle for rectangle center
        LayerUtils.Handle {
            id: handleCenter
            x: rectangleLayer.observation.center.x || 0
            y: rectangleLayer.observation.center.y || 0
            size: getScaledHandleSize()
            scaleRatio: rectangleLayer.scaleRatio
            target: draggableRectangle
            cursorShape: Qt.SizeAllCursor
            visible: rectangleLayer.editable && rectangleLayer.selected
            onMoved: rectangleLayer.commitMove()
        }

        // Handle for rectangle width
        LayerUtils.Handle {
            id: handleWidth
            x: rectangleLayer.observation.center.x + (rectangleLayer.observation.size.width * 0.5)  || 0
            y: handleCenter.y  || 0
            size: getScaledHandleSize()
            scaleRatio: rectangleLayer.scaleRatio
            yAxisEnabled: false
            cursorShape: Qt.SizeHorCursor
            visible: rectangleLayer.editable && rectangleLayer.selected
            onMoved: {
                _currentScene.setObservationFromName(rectangleLayer.name, _currentScene.selectedViewId, { 
                    size: {
                        width: rectangleWidth,
                        height: rectangleHeight 
                    }
                })
            }
        }

        // Handle for rectangle height
        LayerUtils.Handle {
            id: handleHeight
            x: rectangleLayer.observation.center.x || 0
            y: rectangleLayer.observation.center.y - (rectangleLayer.observation.size.height * 0.5)  || 0
            size: getScaledHandleSize()
            scaleRatio: rectangleLayer.scaleRatio
            xAxisEnabled: false
            cursorShape: Qt.SizeVerCursor
            visible: rectangleLayer.editable && rectangleLayer.selected
            onMoved: {
                _currentScene.setObservationFromName(rectangleLayer.name, _currentScene.selectedViewId, { 
                    size: {
                        width: rectangleWidth,
                        height: rectangleHeight 
                    }
                })
            }
        }
    }
}