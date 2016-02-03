import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0

Item {

    id: root
    property variant visualModel: null
    property real thumbnailSize: 130

    ScrollView {
        id: scrollview
        anchors.fill: parent
        ColumnLayout {
            width: scrollview.width
            height: gridview.contentHeight + 20
            spacing: 0
            Item {
                Layout.fillWidth: true
                Layout.preferredHeight: gridview.contentHeight + 20 // + gridview margins
                GridView {
                    id: gridview
                    anchors.fill: parent
                    anchors.margins: 10
                    cellWidth: root.thumbnailSize
                    cellHeight: root.thumbnailSize
                    model: visualModel.parts.grid
                    interactive: false
                    clip: true
                    onCurrentIndexChanged: positionViewAtIndex(currentIndex, GridView.Contain)
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
                minimumValue: 100
                maximumValue: 500
                value: 130
                onValueChanged: root.thumbnailSize = value
            }
        }
    }
}
