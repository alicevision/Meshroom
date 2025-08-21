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
*/
Rectangle {
    id: root

    // handle moved signal
    signal moved()
    
    // handle display size
    property real size : 10.0

    // handle drag target
    property alias target: dragHandler.target

    // handle drag x-axis enabled
    property bool xAxisEnabled : true

    // handle drag y-axis enabled
    property bool yAxisEnabled : true

    // handle cursor shape
    property alias cursorShape : dragHandler.cursorShape

    // handle does not have a true size
    // width and height should always be 0
    width: 0
    height: 0

    // handle hover handler
    HoverHandler {
        cursorShape: dragHandler.cursorShape
        grabPermissions: PointerHandler.CanTakeOverFromAnything  
        margin: size * 2 // handle interaction area
        enabled: root.visible
    }

    // handle drag handler
    DragHandler {
        id: dragHandler
        cursorShape: Qt.SizeBDiagCursor
        grabPermissions: PointerHandler.CanTakeOverFromAnything 
        xAxis.enabled: root.xAxisEnabled
        yAxis.enabled: root.yAxisEnabled
        margin: size * 2 // handle interaction area
        onActiveChanged: { if (!active) { root.moved() } }
        enabled: root.visible
    }

    // handle shape
    Rectangle {
        x: root.size * -0.5
        y: root.size * -0.5
        width: root.size
        height: root.size
        color: "#ffffff"
    }
}