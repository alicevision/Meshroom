import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0

Item {

    id: root
    property variant visualModel: null
    property real thumbnailSize: 60

    ScrollView {
        id: scrollview
        anchors.fill: parent
        ColumnLayout {
            width: scrollview.width
            height: listview.contentHeight + 20
            spacing: 0
            Item {
                Layout.fillWidth: true
                Layout.preferredHeight: listview.contentHeight + 20 // + listview margins
                ListView {
                    id: listview
                    property alias cellHeight: root.thumbnailSize
                    anchors.fill: parent
                    anchors.margins: 10
                    model: visualModel.parts.detail
                    spacing: 1
                    interactive: false
                    clip: true
                    onCurrentIndexChanged: positionViewAtIndex(currentIndex, ListView.Contain)
                }
            }
        }
    }

    Item {
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        width: 200
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
                minimumValue: 45
                maximumValue: 200
                value: 60
                onValueChanged: root.thumbnailSize = value
            }
        }
    }
}
