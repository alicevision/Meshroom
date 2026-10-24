import QtQuick

/**
* MoveArea
*
* @biref Shape area to select a shape and move it directly.
*        Press selects the shape and drag moves it.
* @param shapeLayer - the shape layer (BaseLayer)
*/
MouseArea {
    id: root

    // Shape moved signal, the layer commits the move of its moveTarget
    signal moved()

    // Shape layer
    required property var shapeLayer

    acceptedButtons: Qt.LeftButton
    cursorShape: shapeLayer.editable ? Qt.SizeAllCursor : Qt.ArrowCursor
    enabled: shapeLayer.editable
    drag.target: shapeLayer.moveTarget
    drag.smoothed: false  // Follow the cursor exactly, without losing the drag threshold distance
    drag.threshold: Qt.styleHints.startDragDistance * shapeLayer.scaleRatio  // In image coordinates, keep it constant on screen whatever the zoom

    onPressed: shapeLayer.selectionRequested()

    onReleased: {
        // Moved beyond the drag threshold: commit the move
        // Note: the layer is rebuilt on observation change, which resets the drag offset
        if (shapeLayer.moveTarget.x !== 0 || shapeLayer.moveTarget.y !== 0)
            root.moved()
    }
}
