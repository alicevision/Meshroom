import QtQuick

/**
* PointLayer
*
* @biref Allows to display and modify a 2d point.
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

    property real size: getScaledPointSize()

    // point shape
    Rectangle {
        id: draggablePoint
        x: root.observation.x - (size * 0.5)
        y: root.observation.y - (size * 0.5)
        width: size
        height: width
        color: root.selected ? "#ffffff" : root.properties.color || root.defaultColor

        // selection click
        TapHandler {
            acceptedButtons: Qt.LeftButton
            gesturePolicy: TapHandler.WithinBounds
            grabPermissions: PointerHandler.CanTakeOverFromAnything 
            onTapped: root.selectionRequested()
            enabled: root.editable && !root.selected
        }
        
        // selection hover
        HoverHandler {
            cursorShape: root.selected ? Qt.SizeAllCursor : Qt.PointingHandCursor
            grabPermissions: PointerHandler.CanTakeOverFromAnything 
            enabled: root.editable
        }

        // drag
        DragHandler {
            target: draggablePoint
            cursorShape: Qt.SizeAllCursor
            enabled: root.editable && root.selected
            onActiveChanged: { 
                if (!active) { 
                    ShapeEditor.updateCurrentObservation(root.name, { 
                        x: draggablePoint.x + root.size * 0.5, 
                        y: draggablePoint.y + root.size * 0.5
                    })
                }
            }
        }
    }
}












