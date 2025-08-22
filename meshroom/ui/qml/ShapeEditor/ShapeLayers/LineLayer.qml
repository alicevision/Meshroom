import QtQuick
import QtQuick.Shapes

import "ShapeUtils" as ShapeUtils

/**
* LineLayer
*
* @biref Allows to display and modify a line.
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

    // line shape
    Shape {
        id: draggableLine

        // line path
        ShapePath {
            strokeColor: root.properties.strokeColor || root.properties.color || root.defaultColor
            strokeWidth: getScaledStrokeWidth()
            PathMove { x: handleP1.x; y: handleP1.y }
            PathLine { x: handleP2.x; y: handleP2.y }
        }

        // selection area
        MouseArea  {
            x: Math.min(handleP1.x, handleP2.x)
            y: Math.min(handleP1.y, handleP2.y)
            width: Math.max(handleP1.x, handleP2.x) 
            height: Math.max(handleP1.y, handleP2.y)
            acceptedButtons: Qt.LeftButton
            cursorShape: root.editable ? Qt.PointingHandCursor : Qt.ArrowCursor
            onClicked: root.selectionRequested()
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
            onMoved: {
                ShapeEditor.updateCurrentObservation(root.name, { 
                    x1: handleP1.x + draggableLine.x,
                    y1: handleP1.y + draggableLine.y,
                })
            }
        }

        // handle for p2
        ShapeUtils.Handle {
            id: handleP2
            x: root.observation.x2 || 0
            y: root.observation.y2 || 0
            size: getScaledHandleSize()
            cursorShape: Qt.SizeAllCursor
            visible: root.editable && root.selected
            onMoved: {
                ShapeEditor.updateCurrentObservation(root.name, { 
                    x2: handleP2.x + draggableLine.x,
                    y2: handleP2.y + draggableLine.y,
                })
            }
        }

        // handle for line center
        ShapeUtils.Handle {
            id: handleCenter
            x: (handleP1.x + handleP2.x) * 0.5
            y: (handleP1.y + handleP2.y) * 0.5
            size: getScaledHandleSize()
            target: draggableLine
            cursorShape: Qt.SizeAllCursor
            visible: root.editable && root.selected
            onMoved: {
                ShapeEditor.updateCurrentObservation(root.name, { 
                    x1: handleP1.x + draggableLine.x,
                    y1: handleP1.y + draggableLine.y,
                    x2: handleP2.x + draggableLine.x,
                    y2: handleP2.y + draggableLine.y,
                })
            }
        }
    }
}
