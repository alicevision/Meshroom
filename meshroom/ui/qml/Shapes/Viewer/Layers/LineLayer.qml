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

    // Line center from handleA and handleB position
    property point lineCenter: Qt.point((handleA.x + handleB.x) * 0.5, (handleA.y + handleB.y) * 0.5)
    // Line angle from handleA and handleB position
    property real lineAngle: Math.atan2(handleB.y - handleA.y, handleB.x - handleA.x)
    // Line distance from handleA and handleB position
    property real lineDistance: Math.max(1.0, Math.sqrt(Math.pow(handleA.x - handleB.x, 2) +
                                                        Math.pow(handleA.y - handleB.y, 2)))

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

        // Selection area
        MouseArea  {
            x: Math.min(handleA.x, handleB.x)
            y: Math.min(handleA.y, handleB.y)
            width: Math.abs(handleA.x - handleB.x) 
            height: Math.abs(handleA.y - handleB.y)
            acceptedButtons: Qt.LeftButton
            cursorShape: lineLayer.editable ? Qt.PointingHandCursor : Qt.ArrowCursor
            onClicked: selectionRequested()
            enabled: lineLayer.editable && !lineLayer.selected
        }

        // Handle for point A
        LayerUtils.Handle {
            id: handleA
            x: lineLayer.observation.a.x || 0
            y: lineLayer.observation.a.y || 0
            size: getScaledHandleSize()
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
            target: draggableLine
            cursorShape: Qt.SizeAllCursor
            visible: lineLayer.editable && lineLayer.selected
            onMoved: {
                _currentScene.setObservationFromName(lineLayer.name, _currentScene.selectedViewId, { 
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
        }
    }
}
