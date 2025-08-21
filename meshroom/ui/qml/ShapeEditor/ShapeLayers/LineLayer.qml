import QtQuick
import QtQuick.Shapes

import "ShapeUtils" as ShapeUtils

/**
* LineLayer
*
* @biref Allows to display and modify a line.
* @param modelIndex - the given shape index
* @param properties - the given shape style properties
* @param observation - the given shape position and dimensions for the current view
* @param editable - the shape is editable
* @param selected - the shape is selected
* @param scaleRatio - the shape container scale ratio (scroll zoom)
* @see BaseShapeLayer.qml
*/
BaseShapeLayer {
    id: root

    // line shape
    Shape {
        id: lineShape

        // line path
        ShapePath {
            strokeColor: root.properties.strokeColor || root.properties.color || root.defaultColor
            strokeWidth: getScaledStrokeWidth()
            PathMove { x: handleP1.x; y: handleP1.y }
            PathLine { x: handleP2.x; y: handleP2.y }
        }

        // selection click
        TapHandler {
            acceptedButtons: Qt.LeftButton
            onTapped: { root.selected = (root.editable ? true : false); }
            enabled: root.editable && !root.selected
        }

        // selection hover
        HoverHandler {
            cursorShape: Qt.PointingHandCursor
            enabled: root.editable && !root.selected
        }

        // handle for p1
        ShapeUtils.Handle {
            id: handleP1
            x: root.observation.x1 || 0
            y: root.observation.y1 || 0
            size: getScaledHandleSize()
            cursorShape: Qt.SizeAllCursor
            visible: root.editable && root.selected
        }

        // handle for p2
        ShapeUtils.Handle {
            id: handleP2
            x: root.observation.x2 || 0
            y: root.observation.y2 || 0
            size: getScaledHandleSize()
            cursorShape: Qt.SizeAllCursor
            visible: root.editable && root.selected
        }

        // handle for line center
        ShapeUtils.Handle {
            id: handleCenter
            x: (handleP1.x + handleP2.x) * 0.5
            y: (handleP1.y + handleP2.y) * 0.5
            size: getScaledHandleSize()
            target: lineShape
            cursorShape: Qt.SizeAllCursor
            visible: root.editable && root.selected
        }
    }
}
