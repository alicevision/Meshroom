import QtQuick
import QtQuick.Shapes

import "Utils" as LayerUtils

/**
* LineLayer
*
* @biref Allows to display and modify a line.
* @param name - the given shape name
* @param properties - the given shape style properties
* @param observation - the given shape position and dimensions for the current view
* @param editable - the shape is editable
* @param scaleRatio - the shape container scale ratio (scroll zoom)
* @param selected - the shape is selected
* @see BaseLayer.qml
*/
BaseLayer {
    id: lineLayer
    moveTarget: draggableLine

    // Line center from handleA and handleB position
    property point lineCenter: Qt.point((handleA.x + handleB.x) * 0.5, (handleA.y + handleB.y) * 0.5)
    // Line angle from handleA and handleB position
    property real lineAngle: Math.atan2(handleB.y - handleA.y, handleB.x - handleA.x)
    // Line distance from handleA and handleB position
    property real lineDistance: Math.max(1.0, Math.sqrt(Math.pow(handleA.x - handleB.x, 2) +
                                                        Math.pow(handleA.y - handleB.y, 2)))

    // Commit the move of the line
    function commitMove() {
        _currentScene.setObservationFromName(name, _currentScene.selectedViewId, {
            a: {
                x: handleA.x + draggableLine.x,
                y: handleA.y + draggableLine.y
            },
            b: {
                x: handleB.x + draggableLine.x,
                y: handleB.y + draggableLine.y
            }
        })
    }

    // Line shape
    Shape {
        id: draggableLine

        // Line path
        ShapePath {
            fillColor: "transparent"
            strokeColor: lineLayer.properties.strokeColor || lineLayer.properties.color || lineLayer.defaultColor
            strokeWidth: getScaledStrokeWidth()

            // Line
            PathMove { x: handleA.x; y: handleA.y }
            PathLine { x: handleB.x; y: handleB.y }

            // Orientation center arrow
            PathMove {
                x: lineCenter.x - lineDistance * 0.1 * Math.cos(lineAngle - Math.PI * 0.25)
                y: lineCenter.y - lineDistance * 0.1 * Math.sin(lineAngle - Math.PI * 0.25)
            }
            PathLine { x: lineCenter.x; y: lineCenter.y }
            PathLine { 
                x: lineCenter.x - lineDistance * 0.1 * Math.cos(lineAngle + Math.PI * 0.25)
                y: lineCenter.y - lineDistance * 0.1 * Math.sin(lineAngle + Math.PI * 0.25)
            }
        }

        // Selection and move area: a strip along the line, with a constant thickness on screen
        // Note: the line bounding box would be empty for a horizontal or vertical line
        LayerUtils.MoveArea {
            x: lineCenter.x - width * 0.5
            y: lineCenter.y - height * 0.5
            width: lineDistance
            height: getScaledHandleSize() * 2
            rotation: lineAngle * 180 / Math.PI
            shapeLayer: lineLayer
            onMoved: lineLayer.commitMove()
        }

        // Handle for point A
        LayerUtils.Handle {
            id: handleA
            x: lineLayer.observation.a.x || 0
            y: lineLayer.observation.a.y || 0
            size: getScaledHandleSize()
            scaleRatio: lineLayer.scaleRatio
            cursorShape: Qt.SizeAllCursor
            visible: lineLayer.editable && lineLayer.selected
            onMoved: {
                _currentScene.setObservationFromName(lineLayer.name, _currentScene.selectedViewId, {
                    a: {
                        x: handleA.x + draggableLine.x,
                        y: handleA.y + draggableLine.y
                    }
                })
            }
        }

        // Handle for point B
        LayerUtils.Handle {
            id: handleB
            x: lineLayer.observation.b.x || 0
            y: lineLayer.observation.b.y || 0
            size: getScaledHandleSize()
            scaleRatio: lineLayer.scaleRatio
            cursorShape: Qt.SizeAllCursor
            visible: lineLayer.editable && lineLayer.selected
            onMoved: {
                _currentScene.setObservationFromName(lineLayer.name, _currentScene.selectedViewId, { 
                    b: {
                        x: handleB.x + draggableLine.x,
                        y: handleB.y + draggableLine.y
                    }
                })
            }
        }

        // Handle for line center
        LayerUtils.Handle {
            id: handleCenter
            x: lineCenter.x
            y: lineCenter.y
            size: getScaledHandleSize()
            scaleRatio: lineLayer.scaleRatio
            target: draggableLine
            cursorShape: Qt.SizeAllCursor
            visible: lineLayer.editable && lineLayer.selected
            onMoved: lineLayer.commitMove()
        }
    }
}
