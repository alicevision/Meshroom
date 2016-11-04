import QtQuick 2.7
import QtQuick.Layouts 1.3
import QtQuick.Controls 2.0

Item {

    property real initialOffset: 0.3
    property int minimumSize: 0
    property int handleSize: 2
    property int orientation: Qt.Horizontal
    property Component first: null
    property Component second: null

    Item {
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: (orientation==Qt.Horizontal)? parent.bottom : handle.top
        anchors.right: (orientation==Qt.Horizontal)? handle.left : parent.right
        Loader {
            anchors.fill: parent
            sourceComponent: first
            focus: true
            clip: true
        }
    }
    Rectangle {
        id: handle
        width: (orientation==Qt.Horizontal)? handleSize : parent.width
        height: (orientation==Qt.Horizontal)? parent.height : handleSize
        x: (orientation==Qt.Horizontal)? parent.width * initialOffset : 0
        y: (orientation==Qt.Horizontal)? 0 : parent.height * initialOffset
        color: "#5BB1F7"
        opacity: (handleMouseArea.containsMouse || handleMouseArea.pressed) ? 1 : 0
        Behavior on opacity { NumberAnimation{} }
        MouseArea {
            id: handleMouseArea
            anchors.fill: parent
            hoverEnabled: true
            drag {
                target: parent
                axis: (orientation==Qt.Horizontal)? Drag.XAxis : Drag.YAxis
                minimumX: minimumSize
                maximumX: handle.parent.width - handleSize - minimumSize
                minimumY: minimumSize
                maximumY: handle.parent.height - handleSize - minimumSize
                smoothed: true
            }
            cursorShape: (orientation==Qt.Horizontal)? Qt.SplitHCursor : Qt.SplitVCursor
        }
    }
    Item {
        anchors.left: (orientation==Qt.Horizontal)? handle.right : parent.left
        anchors.top: (orientation==Qt.Horizontal)? parent.top : handle.bottom
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        Loader {
            anchors.fill: parent
            sourceComponent: second
            clip: true
        }
    }

}
