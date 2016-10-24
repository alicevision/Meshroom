import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.2


RowLayout {

    property bool isInput: true

    spacing: 2
    Label {
        Layout.fillWidth: true
        text: model.name
        horizontalAlignment: Text.AlignRight
        state: "xsmall"
        visible: !isInput
    }
    Rectangle {
        Layout.fillHeight: true
        Layout.preferredWidth: 1
        color: Qt.rgba(1, 1, 1, 0.5)
        DropArea {
            id: dropArea
            anchors.centerIn: parent
            width: 10
            height: 10
            onDropped: drop.accept()
            Rectangle {
                anchors.centerIn: parent
                width: 10
                height: 10
                radius: 5
                color: "#5BB1F7"
                border.color: "white"
                opacity: dropArea.containsDrag && isInput ? 1 : 0
                Behavior on opacity { NumberAnimation {}}
            }
        }
        Rectangle {
            id: draggable
            anchors.centerIn: parent
            width: 10
            height: 10
            radius: 5
            color: "transparent"
            border.color: "white"
            opacity: dragArea.containsMouse ? 1 : 0
            Behavior on opacity { NumberAnimation {}}
            Drag.active: dragArea.drag.active
            Drag.hotSpot.x: width*0.5
            Drag.hotSpot.y: height*0.5
            visible: !isInput
            MouseArea {
                id: dragArea
                anchors.fill: parent
                drag.target: parent
                drag.threshold: 0
            }
        }
    }
    Label {
        Layout.fillWidth: true
        text: model.name
        horizontalAlignment: Text.AlignLeft
        state: "xsmall"
        visible: isInput
    }

}
