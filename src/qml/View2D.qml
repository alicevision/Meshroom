import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3

Rectangle {

    id: root
    color: Qt.rgba(0, 0, 0, 0.2)

    Rectangle {
        anchors.centerIn: parent
        width: Math.min(parent.width, parent.height*1.333) * 0.95 // 5% margin
        height: Math.min(parent.height, parent.width*0.75) * 0.95 // 5% margin
        color: "transparent"
        border.color: "#666"
    }

}
