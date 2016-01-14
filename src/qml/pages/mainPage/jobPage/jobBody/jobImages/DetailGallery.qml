import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0
import "../../../../../delegates"

Item {

    id: root
    property variant visualModel: null
    property real thumbnailSize: 50

    ListView {
        anchors.fill: parent
        property alias cellHeight: root.thumbnailSize
        spacing: 1
        model: visualModel.parts.detail
        clip: true
        Component.onCompleted: forceActiveFocus()
        onCurrentIndexChanged: positionViewAtIndex(currentIndex, ListView.Contain)
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
                minimumValue: 30
                maximumValue: 200
                value: 50
                onValueChanged: root.thumbnailSize = value
            }
            // ToolButton {
            //     iconSource: "qrc:///images/disk.svg"
            // }
        }
    }
}
