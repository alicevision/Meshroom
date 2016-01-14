import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0
import "../../../../../delegates"

Item {

    id: root
    property variant visualModel: null
    property real thumbnailSize: 130

    GridView {
        anchors.fill: parent
        anchors.margins: 10
        cellWidth: root.thumbnailSize
        cellHeight: root.thumbnailSize
        model: visualModel.parts.grid
        clip: true
        Component.onCompleted: forceActiveFocus()
        onCurrentIndexChanged: positionViewAtIndex(currentIndex, GridView.Contain)
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
            // ToolButton {
            //     iconSource: "qrc:///images/disk.svg"
            // }
        }
    }
}
