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

    // Line shape
    Shape {
        id: draggableLine

        // Line path
        ShapePath {
            strokeColor: lineLayer.properties.strokeColor || lineLayer.properties.color || lineLayer.defaultColor
            strokeWidth: getScaledStrokeWidth()
            PathMove { x: handleA.x; y: handleA.y }
            PathLine { x: handleB.x; y: handleB.y }
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
                _reconstruction.setObservationFromName(lineLayer.name, _reconstruction.selectedViewId, {
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
                _reconstruction.setObservationFromName(lineLayer.name, _reconstruction.selectedViewId, { 
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
            x: (handleA.x + handleB.x) * 0.5
            y: (handleA.y + handleB.y) * 0.5
            size: getScaledHandleSize()
            target: draggableLine
            cursorShape: Qt.SizeAllCursor
            visible: lineLayer.editable && lineLayer.selected
            onMoved: {
                _reconstruction.setObservationFromName(lineLayer.name, _reconstruction.selectedViewId, { 
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
