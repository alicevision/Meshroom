import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3

Item {

    id: root

    // properties
    property variant visualModel: null
    property real thumbnailSize: 130

    // gridview
    GridView {
        id: gridview
        anchors.fill: parent
        anchors.margins: 2
        ScrollBar.vertical: ScrollBar {}
        cellWidth: root.thumbnailSize
        cellHeight: root.thumbnailSize
        model: visualModel.parts.grid
        clip: true
    }

    // bottom menu
    Item {
        anchors.bottom: parent.bottom
        width: parent.width
        height: 30
        Rectangle {
            anchors.fill: parent
            color: Qt.rgba(0, 0, 0, 0.3)
        }
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 4
            anchors.rightMargin: 4
            spacing: 0
            Slider {
                Layout.fillWidth: true
                from: 50
                to: 150
                value: 60
                onPositionChanged: root.thumbnailSize = from+(to-from)*position
            }
        }
    }
}
