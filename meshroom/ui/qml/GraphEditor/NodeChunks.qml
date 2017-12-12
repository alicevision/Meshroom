import QtQuick 2.7


ListView {
    id: root
    interactive: false

    SystemPalette { id: palette }

    property color defaultColor: Qt.darker(palette.window, 1.1)
    property real chunkHeight: height
    property real chunkWidth: model ? width / model.count : 0
    orientation: ListView.Horizontal
    implicitWidth: 100
    spacing: 0
    delegate: Rectangle {
        id: chunkDelegate
        height: root.chunkHeight
        width: root.chunkWidth
        state: object.statusName
        states: [
            State { name: "NONE"; PropertyChanges { target: chunkDelegate; color: root.defaultColor } },
            State { name: "SUBMITTED"; PropertyChanges { target: chunkDelegate; color: object.execModeName == "LOCAL" ? "#009688" : "#2196F3"} },
            State { name: "RUNNING"; PropertyChanges { target: chunkDelegate; color: "#FF9800"} },
            State { name: "ERROR"; PropertyChanges { target: chunkDelegate; color: "#F44336"} },
            State { name: "SUCCESS"; PropertyChanges { target: chunkDelegate; color: "#4CAF50"} }
        ]
    }
}

