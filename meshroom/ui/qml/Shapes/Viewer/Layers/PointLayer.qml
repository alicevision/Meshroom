import QtQuick

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

    // Point size from scaled properties.size
    property real pointSize: pointLayer.getScaledPointSize()

    // Point shape
    Rectangle {
        id: draggablePoint
        x: pointLayer.observation.x - (pointSize * 0.5)
        y: pointLayer.observation.y - (pointSize * 0.5)
        width: pointSize
        height: width
        color: selected ? "#ffffff" : pointLayer.properties.color || pointLayer.defaultColor

        // Selection click
        TapHandler {
            acceptedButtons: Qt.LeftButton
            gesturePolicy: TapHandler.WithinBounds
            grabPermissions: PointerHandler.CanTakeOverFromAnything 
            onTapped: selectionRequested()
            enabled: pointLayer.editable && !pointLayer.selected
        }
        
        // Selection hover
        HoverHandler {
            cursorShape: pointLayer.selected ? Qt.SizeAllCursor : Qt.PointingHandCursor
            grabPermissions: PointerHandler.CanTakeOverFromAnything 
            enabled: pointLayer.editable
        }

        // Drag
        DragHandler {
            target: draggablePoint
            cursorShape: Qt.SizeAllCursor
            enabled: pointLayer.editable && pointLayer.selected
            onActiveChanged: { 
                if (!active) { 
                    _reconstruction.setObservationFromName(pointLayer.name, _reconstruction.selectedViewId, { 
                        x: draggablePoint.x + pointSize * 0.5, 
                        y: draggablePoint.y + pointSize * 0.5
                    })
                }
            }
        }
    }
}












