import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0

Item {

    id: root

    // properties
    property variant visualModel: null
    property real thumbnailSize: 130

    // scroll & gridview
    ScrollView {
        id: scrollview
        anchors.fill: parent
        GridView {
            id: gridview
            anchors.fill: parent
            anchors.margins: 2
            cellWidth: root.thumbnailSize
            cellHeight: root.thumbnailSize
            model: visualModel.parts.grid
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
                minimumValue: 50
                maximumValue: 150
                value: 60
                onValueChanged: root.thumbnailSize = value
            }
        }
    }
}
