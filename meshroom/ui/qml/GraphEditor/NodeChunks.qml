import QtQuick 2.7
import Utils 1.0

//import "common.js" as Common

ListView {
    id: root
    interactive: false

    SystemPalette { id: activePalette }

    property color defaultColor: Qt.darker(activePalette.window, 1.1)
    property real chunkHeight: height
    property real chunkWidth: model ? width / model.count : 0

    orientation: ListView.Horizontal
    implicitWidth: 100
    spacing: 0
    delegate: Rectangle {
        id: chunkDelegate
        height: root.chunkHeight
        width: root.chunkWidth
        color: Colors.getChunkColor(object, {"NONE": root.defaultColor})
    }
}

