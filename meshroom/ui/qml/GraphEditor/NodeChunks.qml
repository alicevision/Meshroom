import QtQuick

import Utils 1.0

ListView {
    id: root
    interactive: false
    property bool highlightChunks: true

    SystemPalette { id: activePalette }

    property color defaultColor: Qt.darker(activePalette.window, 1.1)
    property real chunkHeight: height
    property bool modelIsBig: (3 * model.count >= width)
    property real chunkWidth: {
        if (!model || model.count == 0)
            return 0
        return (width / model.count) - spacing
    }

    orientation: ListView.Horizontal

    // If we have enough space, add one pixel margin between chunks
    spacing: modelIsBig ? 0 : 1
    delegate: Rectangle {
        id: chunkDelegate
        height: root.chunkHeight
        width: root.chunkWidth
        property var chunkColor: Colors.getChunkColor(object, { "NONE": root.defaultColor })
        color: {
            if (!highlightChunks || model.count == 1)
                return chunkColor
            if (index % 2 == 0)
                return Qt.lighter(chunkColor, 1.1)
            else
                return Qt.darker(chunkColor, 1.1)
        }
    }
}
