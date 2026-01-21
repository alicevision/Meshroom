import QtQuick
import QtQuick.Shapes

import "Utils" as LayerUtils

/**
* CircleLayer
*
* @biref Allows to display and modify a circle.
* @param name - the given shape name
* @param properties - the given shape style properties
* @param observation - the given shape position and dimensions for the current view
* @param editable - the shape is editable
* @param scaleRatio - the shape container scale ratio (scroll zoom)
* @param selected - the shape is selected
* @see BaseLayer.qml
*/
BaseLayer {
    id: circleLayer

    // Circle radius from handleRadius position
    property real circleRadius: Math.max(1.0, Math.sqrt(Math.pow(handleRadius.x - handleCenter.x, 2) +
                                                        Math.pow(handleRadius.y - handleCenter.y, 2)))
                                     
    // Circle shape
    Shape {
        id: draggableShape

        // Circle path
        ShapePath {
            fillColor: circleLayer.properties.fillColor || "transparent"
            strokeColor: circleLayer.properties.strokeColor || circleLayer.properties.color || circleLayer.defaultColor
            strokeWidth: getScaledStrokeWidth()

            // Circle
            PathRectangle {
                x: circleLayer.observation.center.x - circleRadius
                y: circleLayer.observation.center.y - circleRadius
                width: circleRadius * 2
                height: circleRadius * 2
                radius: circleRadius
            }

            // Center cross
            PathMove { x: circleLayer.observation.center.x - 10; y: circleLayer.observation.center.y }
            PathLine { x: circleLayer.observation.center.x + 10; y: circleLayer.observation.center.y }
            PathMove { x: circleLayer.observation.center.x; y: circleLayer.observation.center.y - 10 }
            PathLine { x: circleLayer.observation.center.x; y: circleLayer.observation.center.y + 10 }
        }

        // Radius helper path
        ShapePath {
            fillColor: "transparent"
            strokeColor: circleLayer.selected ? "#bbffffff" : "transparent"
            strokeWidth: getScaledHelperStrokeWidth()

            PathMove { x: circleLayer.observation.center.x; y: circleLayer.observation.center.y }
            PathLine { x: handleRadius.x; y: handleRadius.y }
        }

        // Selection area
        MouseArea  {
            x: handleCenter.x - circleRadius
            y: handleCenter.y - circleRadius
            width: circleRadius * 2
            height: circleRadius * 2
            acceptedButtons: Qt.LeftButton
            cursorShape: circleLayer.editable ? Qt.PointingHandCursor : Qt.ArrowCursor
            onClicked: selectionRequested()
            enabled: circleLayer.editable && !circleLayer.selected
        }
        
        // Handle for circle center
        LayerUtils.Handle {
            id: handleCenter
            x: circleLayer.observation.center.x || 0
            y: circleLayer.observation.center.y || 0
            size: getScaledHandleSize()
            target: draggableShape
            cursorShape: Qt.SizeAllCursor
            visible: circleLayer.editable && circleLayer.selected
            onMoved: {
                _currentScene.setObservationFromName(circleLayer.name, _currentScene.selectedViewId, { 
                    center: {
                        x: handleCenter.x + draggableShape.x, 
                        y: handleCenter.y + draggableShape.y 
                    } 
                })
            }
        }

        // Handle for circle radius
        LayerUtils.Handle {
            id: handleRadius
            x: circleLayer.observation.center.x + circleLayer.observation.radius || 0
            y: circleLayer.observation.center.y || 0
            size: getScaledHandleSize()
            cursorShape: Qt.SizeBDiagCursor
            visible: circleLayer.editable && circleLayer.selected
            onMoved: {
                _currentScene.setObservationFromName(circleLayer.name, _currentScene.selectedViewId, { 
                    radius: circleRadius 
                })
            }
        }
    }
}

