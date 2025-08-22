import QtQuick
import QtQuick.Shapes

import "ShapeUtils" as ShapeUtils

/**
* RectangleLayer
*
* @biref Allows to display and modify a rectangle.
* @param name - the given shape name
* @param properties - the given shape style properties
* @param observation - the given shape position and dimensions for the current view
* @param editable - the shape is editable
* @param selected - the shape is selected
* @param scaleRatio - the shape container scale ratio (scroll zoom)
* @see BaseShapeLayer.qml
*/
BaseShapeLayer {
    id: root

    // rectangle width from handleWidth position
    property real rectangleWidth: Math.max(1.0, Math.abs(root.observation.centerX - handleWidth.x) * 2)

    // rectangle height from handleHeight position
    property real rectangleHeight: Math.max(1.0, Math.abs(root.observation.centerY - handleHeight.y) * 2)

    // rectangle shape
    Shape {
        id : rectangleShape

        // rectangle path 
        ShapePath {
            fillColor: root.properties.fillColor || "transparent"
            strokeColor: root.properties.strokeColor || root.properties.color || root.defaultColor
            strokeWidth: getScaledStrokeWidth()

            PathRectangle {
                x: root.observation.centerX - (rectangleWidth * 0.5)
                y: root.observation.centerY - (rectangleHeight * 0.5)
                width: rectangleWidth
                height: rectangleHeight
            }
        }

        // size helper path
        ShapePath {
            fillColor: "transparent"
            strokeColor: root.selected ? "#bbffffff" : "transparent"
            strokeWidth: getScaledHelperStrokeWidth()

            PathMove { x: root.observation.centerX; y: root.observation.centerY }
            PathLine { x: handleWidth.x; y: handleWidth.y }
            PathMove { x: root.observation.centerX; y: root.observation.centerY }
            PathLine { x: handleHeight.x; y: handleHeight.y }
        }

        // selection area
        MouseArea  {
            x: handleCenter.x - rectangleWidth * 0.5
            y: handleCenter.y - rectangleHeight * 0.5
            width: rectangleWidth
            height: rectangleHeight
            acceptedButtons: Qt.LeftButton
            cursorShape: Qt.PointingHandCursor
            onClicked: root.selectionRequested()
            enabled: root.editable && !root.selected
        }

        // handle for rectangle center
        ShapeUtils.Handle {
            id: handleCenter
            x: root.observation.centerX || 0
            y: root.observation.centerY || 0
            size: getScaledHandleSize()
            target: rectangleShape
            cursorShape: Qt.SizeAllCursor
            visible: root.editable && root.selected
        }

        // handle for rectangle width
        ShapeUtils.Handle {
            id: handleWidth
            x: root.observation.centerX + (root.observation.width * 0.5)  || 0
            y: handleCenter.x  || 0
            size: getScaledHandleSize()
            yAxisEnabled: false
            cursorShape: Qt.SizeHorCursor
            visible: root.editable && root.selected
        }

        // handle for rectangle height
        ShapeUtils.Handle {
            id: handleHeight
            x: root.observation.centerX || 0
            y: root.observation.centerY - (root.observation.height * 0.5)  || 0
            size: getScaledHandleSize()
            xAxisEnabled: false
            cursorShape: Qt.SizeVerCursor
            visible: root.editable && root.selected
        }
    }
}