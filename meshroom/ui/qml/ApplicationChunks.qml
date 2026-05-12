import QtQuick

import Utils 1.0

ListView {
    id: root
    interactive: false

    SystemPalette { id: activePalette }

    property color defaultColor: Qt.darker(activePalette.window, 1.1)
    property int modelSize: model ? model.count : 0
    property bool modelIsBig: (3 * modelSize >= width)
    property real chunkWidth: {
        if (modelSize == 0) return 0
        return (width / modelSize) - spacing
    }

    orientation: ListView.Horizontal

    // If we have enough space, add one pixel margin between chunks
    spacing: modelIsBig ? 0 : 1
    delegate: Rectangle {
        id: chunkDelegate
        height: root.height
        width: root.chunkWidth
        property var chunkColor: Colors.getChunkColor(object, { "NONE": root.defaultColor })
        color: {
            if (index % 2 == 0)
                return Qt.lighter(chunkColor, 1.1)
            else
                return Qt.darker(chunkColor, 1.1)
        }
    }
}