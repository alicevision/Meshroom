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
    id: surveyPointLayer

    // Point size and half size
    property real pointSize: Math.max(1.0, 12.0 * scaleRatio)
    property real pointHalfSize: pointSize * 0.5

    // Point shape
    Shape {
        id: draggableShape

        // Center cross path
        ShapePath {
            fillColor: "transparent"
            strokeColor: selected ? "#ffffff" : surveyPointLayer.properties.color || surveyPointLayer.defaultColor
            strokeWidth: getScaledStrokeWidth()

            PathMove { x: surveyPointLayer.observation.x - pointSize; y: surveyPointLayer.observation.y }
            PathLine { x: surveyPointLayer.observation.x + pointSize; y: surveyPointLayer.observation.y }
            PathMove { x: surveyPointLayer.observation.x; y: surveyPointLayer.observation.y - pointSize }
            PathLine { x: surveyPointLayer.observation.x; y: surveyPointLayer.observation.y + pointSize }
        }

        ShapePath {
            fillColor: "transparent"
            strokeColor: '#b94d0e'
            strokeWidth: getScaledStrokeWidth()

            PathMove { x: surveyPointLayer.observation.x; y: surveyPointLayer.observation.y }
            PathLine {
                x: isNaN(surveyPointLayer.observation.ex) ? surveyPointLayer.observation.x : surveyPointLayer.observation.ex
                y: isNaN(surveyPointLayer.observation.ey) ? surveyPointLayer.observation.y : surveyPointLayer.observation.ey
            }
        }

        // Selection area
        MouseArea  {
            x: handleCenter.x - pointSize
            y: handleCenter.y - pointSize
            width: pointSize * 2
            height: pointSize * 2
            acceptedButtons: Qt.LeftButton
            cursorShape: surveyPointLayer.editable ? Qt.PointingHandCursor : Qt.ArrowCursor
            onClicked: selectionRequested()
            enabled: surveyPointLayer.editable && !surveyPointLayer.selected
        }

        // Handle for point center
        LayerUtils.Handle {
            id: handleCenter
            x: surveyPointLayer.observation.x || 0
            y: surveyPointLayer.observation.y || 0
            size: getScaledHandleSize()
            target: draggableShape
            cursorShape: Qt.SizeAllCursor
            visible: surveyPointLayer.editable && surveyPointLayer.selected
            onMoved: {
                _currentScene.setObservationFromName(surveyPointLayer.name, _currentScene.selectedViewId, { 
                    x: handleCenter.x + draggableShape.x, 
                    y: handleCenter.y + draggableShape.y
                })
            }
        }

        // Point name
        Rectangle {
            x: (surveyPointLayer.observation.x || 0) + pointHalfSize
            y: (surveyPointLayer.observation.y || 0) + pointHalfSize
            width: pointName.width
            height: pointName.height
            visible: surveyPointLayer.editable && scaleRatio > 0.2
            color: selected ? palette.shadow : palette.window

            Text {
                id: pointName
                text: {
                    if(surveyPointLayer.properties.userName && surveyPointLayer.properties.userName.length > 0)
                        return surveyPointLayer.properties.userName
                    const lastDotIndex = surveyPointLayer.name.lastIndexOf('.')
                    if(lastDotIndex < 0)
                        return surveyPointLayer.name
                    return surveyPointLayer.name.substring(lastDotIndex + 1);
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












