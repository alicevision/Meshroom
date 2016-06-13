import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0

Item {

    id: root

    // properties
    property variant visualModel: null
    property real thumbnailSize: 60

    // scroll & listview
    ScrollView {
        id: scrollview
        anchors.fill: parent
        ListView {
            id: listview
            property alias cellHeight: root.thumbnailSize
            anchors.fill: parent
            anchors.margins: 2
            model: visualModel.parts.list
            spacing: 4
            clip: true
        }
    }

    // bottom menu
    Item {
        anchors.bottom: parent.bottom
        width: parent.width
        height: 30
        Rectangle {
            anchors.fill: parent
            opacity: 0.6
            color: Style.window.color.xdark
        }
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 4
            anchors.rightMargin: 4
            spacing: 0
            Slider {
                Layout.fillWidth: true
                minimumValue: 30
                maximumValue: 100
                value: 50
                onValueChanged: root.thumbnailSize = value
            }
        }
    }
}
