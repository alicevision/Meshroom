import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3

Item {

    id: root

    // properties
    property variant visualModel: null
    property real thumbnailSize: 60

    // listview
    ListView {
        id: listview
        property alias cellHeight: root.thumbnailSize
        anchors.fill: parent
        anchors.margins: 2
        ScrollBar.vertical: ScrollBar {}
        model: visualModel.parts.list
        spacing: 4
        clip: true
    }

    // bottom menu
    Item {
        anchors.bottom: parent.bottom
        width: parent.width
        height: 30
        Rectangle {
            anchors.fill: parent
            opacity: 0.6
            color: Qt.rgba(0, 0, 0, 0.3)
        }
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 4
            anchors.rightMargin: 4
            spacing: 0
            Slider {
                Layout.fillWidth: true
                from: 30
                to: 100
                value: 50
                onPositionChanged: root.thumbnailSize = from+(to-from)*position
            }
        }
    }
}
