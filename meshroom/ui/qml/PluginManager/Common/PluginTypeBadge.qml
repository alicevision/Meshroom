import QtQuick
import QtQuick.Controls

/**
 * PluginTypeBadge:
 * A small rounded pill showing a plugin's type.
 */

Rectangle {
    id: root

    property string typeName: ""
    property bool isPending: false

    // Badge Color
    readonly property color baseColor: {
        if (isPending) { return '#008d8d' }
        switch (root.typeName) {
            case "BUILTIN": return '#ffd000'
            case "LOCAL": return '#0044cc'
            case "PATH": return '#cc0000'
            case "REZ": return '#00cc00'
            default: return '#555555'
        }
    }

    // Badge Text
    readonly property string text: {
        if (isPending) { return "pending" }
        switch (root.typeName) {
            case "BUILTIN": return "built-in"
            case "LOCAL": return "installed"
            case "PATH": return "path"
            case "REZ": return "rez"
            default: return "available"
        }
    }

    implicitWidth: label.implicitWidth + 18
    implicitHeight: label.implicitHeight + 6
    radius: height * 0.5

    color: Qt.rgba(root.baseColor.r, root.baseColor.g, root.baseColor.b, 0.4)
    border.color: root.baseColor
    border.width: 1
    
    Label {
        id: label
        anchors.centerIn: parent
        text: root.text
        font.pointSize: 8
    }
}
