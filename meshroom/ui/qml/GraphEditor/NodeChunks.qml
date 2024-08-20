import QtQuick 2.15
import Utils 1.0

//import "common.js" as Common

ListView {
    id: root
    interactive: false

    SystemPalette { id: activePalette }

    property color defaultColor: Qt.darker(activePalette.window, 1.1)
    property real chunkHeight: height
    property bool modelIsBig: (3 * model.count >= width)
    property real chunkWidth: {
        if(!model || model.count == 0)
            return 0
        return (width / model.count) - spacing
    }

    orientation: ListView.Horizontal
    implicitWidth: 100
    // If we have enough space, add one pixel margin between chunks
    spacing: modelIsBig ? 0 : 1
    delegate: Rectangle {
        id: chunkDelegate
        height: root.chunkHeight
        width: root.chunkWidth
        property var chunkColor: Colors.getChunkColor(object, { "NONE": root.defaultColor })
        color: index % 2 == 0 ? chunkColor : Qt.darker(chunkColor, 1.2)
    }
}

