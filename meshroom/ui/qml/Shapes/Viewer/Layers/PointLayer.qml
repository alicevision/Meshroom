import QtQuick
import QtQuick.Shapes

import "Utils" as LayerUtils

/**
* PointLayer
*
* @biref Allows to display and modify a 2d point.
* @param name - the given shape name
* @param properties - the given shape style properties
* @param observation - the given shape position and dimensions for the current view
* @param editable - the shape is editable
* @param scaleRatio - the shape container scale ratio (scroll zoom)
* @param selected - the shape is selected
* @see BaseLayer.qml
*/
BaseLayer {
    id: pointLayer

    // Point size and half size
    property real pointSize: Math.max(1.0, 12.0 * scaleRatio)
    property real pointHalfSize: pointSize * 0.5

    // Point shape
    Shape {
        id: draggableShape

        // Center cross path
        ShapePath {
            fillColor: "transparent"
            strokeColor: selected ? "#ffffff" : pointLayer.properties.color || pointLayer.defaultColor
            strokeWidth: getScaledStrokeWidth()

            PathMove { x: pointLayer.observation.x - pointSize; y: pointLayer.observation.y }
            PathLine { x: pointLayer.observation.x + pointSize; y: pointLayer.observation.y }
            PathMove { x: pointLayer.observation.x; y: pointLayer.observation.y - pointSize }
            PathLine { x: pointLayer.observation.x; y: pointLayer.observation.y + pointSize }
        }

        // Selection area
        MouseArea  {
            x: handleCenter.x - pointSize
            y: handleCenter.y - pointSize
            width: pointSize * 2
            height: pointSize * 2
            acceptedButtons: Qt.LeftButton
            cursorShape: pointLayer.editable ? Qt.PointingHandCursor : Qt.ArrowCursor
            onClicked: selectionRequested()
            enabled: pointLayer.editable && !pointLayer.selected
        }

        // Handle for point center
        LayerUtils.Handle {
            id: handleCenter
            x: pointLayer.observation.x || 0
            y: pointLayer.observation.y || 0
            size: getScaledHandleSize()
            target: draggableShape
            cursorShape: Qt.SizeAllCursor
            visible: pointLayer.editable && pointLayer.selected
            onMoved: {
                _currentScene.setObservationFromName(pointLayer.name, _currentScene.selectedViewId, { 
                    x: handleCenter.x + draggableShape.x, 
                    y: handleCenter.y + draggableShape.y
                })
            }
        }

        // Point name
        Rectangle {
            x: (pointLayer.observation.x || 0) + pointHalfSize
            y: (pointLayer.observation.y || 0) + pointHalfSize
            width: pointName.width
            height: pointName.height
            visible: pointLayer.editable && scaleRatio > 0.2
            color: selected ? palette.shadow : palette.window

            Text {
                id: pointName
                text: {
                    if(pointLayer.properties.userName && pointLayer.properties.userName.length > 0)
                        return pointLayer.properties.userName
                    const lastDotIndex = pointLayer.name.lastIndexOf('.')
                    if(lastDotIndex < 0)
                        return pointLayer.name
                    return pointLayer.name.substring(lastDotIndex + 1);
                }
                color: selected ? palette.highlightedText : palette.text
                padding: 0
                rightPadding: Math.max(1, 2 * scaleRatio)
                leftPadding: rightPadding
                wrapMode: Text.NoWrap 
                font.pixelSize: getScaledFontSize()
            }
        }
    }
}












