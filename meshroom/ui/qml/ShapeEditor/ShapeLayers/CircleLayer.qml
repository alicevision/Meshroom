import QtQuick
import QtQuick.Shapes

import "ShapeUtils" as ShapeUtils

/**
* CircleLayer
*
* @biref Allows to display and modify a circle.
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

    // circle radius from handleRadius position
    property real circleRadius: Math.max(1.0, Math.sqrt(Math.pow(handleRadius.x - handleCenter.x, 2) +
                                                        Math.pow(handleRadius.y - handleCenter.y, 2)))
                                     
    // circle shape
    Shape {
        id: circleShape

        // circle path
        ShapePath {
            fillColor: root.properties.fillColor || "transparent"
            strokeColor: root.properties.strokeColor || root.properties.color || root.defaultColor
            strokeWidth: getScaledStrokeWidth()

            // circle
            PathRectangle {
                x: root.observation.centerX - root.circleRadius
                y: root.observation.centerY - root.circleRadius
                width: root.circleRadius * 2
                height: root.circleRadius * 2
                radius: root.circleRadius
            }

            // center cross
            PathMove { x: root.observation.centerX - 10; y: root.observation.centerY }
            PathLine { x: root.observation.centerX + 10; y: root.observation.centerY }
            PathMove { x: root.observation.centerX; y: root.observation.centerY - 10 }
            PathLine { x: root.observation.centerX; y: root.observation.centerY + 10 }
        }

        // radius helper path
        ShapePath {
            fillColor: "transparent"
            strokeColor: root.selected ? "#bbffffff" : "transparent"
            strokeWidth: getScaledHelperStrokeWidth()

            PathMove { x: root.observation.centerX; y: root.observation.centerY }
            PathLine { x: handleRadius.x; y: handleRadius.y }
        }

        // selection area
        MouseArea  {
            x: handleCenter.x - root.circleRadius
            y: handleCenter.y - root.circleRadius
            width: root.circleRadius * 2
            height: root.circleRadius * 2
            acceptedButtons: Qt.LeftButton
            cursorShape: Qt.PointingHandCursor
            onClicked: root.selectionRequested()
            enabled: root.editable && !root.selected
        }
       
        // handle for circle center
        ShapeUtils.Handle {
            id: handleCenter
            x: root.observation.centerX || 0
            y: root.observation.centerY || 0
            size: getScaledHandleSize()
            target: circleShape
            cursorShape: Qt.SizeAllCursor
            visible: root.editable && root.selected
        }

        // handle for circle radius
        ShapeUtils.Handle {
            id: handleRadius
            x: root.observation.centerX + root.observation.radius || 0
            y: root.observation.centerY || 0
            size: getScaledHandleSize()
            cursorShape: Qt.SizeBDiagCursor
            visible: root.editable && root.selected
        }
    }
}

