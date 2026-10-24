import QtQuick

/**
* Handle
*
* @biref Handle component to centralize handle behavior and avoid code duplication.
* @param size - the handle display size
* @param target - the handle drag target
* @param xAxisEnabled - the handle x-axis is draggable
* @param yAxisEnabled - the handle y-axis is draggable
* @param cursorShape - the handle cursor shape
* @param scaleRatio - the shape container scale ratio (scroll zoom)
*/
Rectangle {
    id: root

    // Handle moved signal
    signal moved()

    // Handle clicked without moving it (the handle takes the presses from the shape selection area)
    signal tapped(int modifiers)
    
    // Handle display size
    property real size : 10.0

    // Handle drag target
    property alias target: dragHandler.target

    // Handle drag x-axis enabled
    property bool xAxisEnabled : true

    // Handle drag y-axis enabled
    property bool yAxisEnabled : true

    // Handle cursor shape
    property alias cursorShape : dragHandler.cursorShape

    // Shape container scale ratio
    property real scaleRatio: 1.0

    // Handle does not have a true size
    // Width and height should always be 0
    width: 0
    height: 0

    // Handle hover handler
    HoverHandler {
        cursorShape: dragHandler.cursorShape
        grabPermissions: PointerHandler.CanTakeOverFromAnything  
        margin: root.size * 2 // Handle interaction area
        enabled: root.visible
    }

    // Handle drag handler
    DragHandler {
        id: dragHandler
        cursorShape: Qt.SizeBDiagCursor
        grabPermissions: PointerHandler.CanTakeOverFromAnything 
        // The drag threshold is compared in the parent (image) coordinates: keep it constant on screen whatever the zoom
        dragThreshold: Qt.styleHints.startDragDistance * root.scaleRatio
        xAxis.enabled: root.xAxisEnabled
        yAxis.enabled: root.yAxisEnabled
        margin: root.size * 2 // Handle interaction area
        onActiveChanged: {
            if (active) {
                // Take the focus so that the 2d Viewer receives key events (e.g. Delete),
                // even if the shape was selected from another panel
                root.forceActiveFocus()
            } else {
                root.moved()
            }
        }
        enabled: root.visible
    }

    // Handle tap handler, canceled when the drag handler moves the handle
    TapHandler {
        acceptedButtons: Qt.LeftButton
        gesturePolicy: TapHandler.DragThreshold
        margin: root.size * 2 // Handle interaction area
        enabled: root.visible
        onTapped: root.tapped(point.modifiers)
    }

    // Handle shape
    Rectangle {
        x: root.size * -0.5
        y: root.size * -0.5
        width: root.size
        height: root.size
        color: "#ffffff"
    }

    // Handle outline
    Rectangle {
        x: width * -0.5
        y: height * -0.5
        width: 1.5 * root.size
        height: 1.5 * root.size
        color: "#66666666"
        z: -1
    }
}