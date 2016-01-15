import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0

Item {

    Rectangle {
        anchors.fill: parent
        anchors.margins: 5
        color: mouseArea.containsMouse ? Style.window.color.selected : Style.window.color.xdark
        Behavior on color { ColorAnimation {} }
        MouseArea {
            id: mouseArea
            anchors.fill: parent
            hoverEnabled: true
            onClicked: selectProject(index)
        }
        ColumnLayout {
            anchors.fill: parent
            spacing: 0
            Item {
                Layout.fillWidth: true
                Layout.preferredHeight: width*3/4.0
                Image {
                    anchors.fill: parent
                    anchors.margins: 4
                    source: model.jobs.get(0).thumbnail
                    asynchronous: true
                }
            }
            Text {
                Layout.fillWidth: true
                Layout.fillHeight: true
                text: model.name
                horizontalAlignment: Text.AlignHCenter
            }

        }
        ToolButton {
            anchors.horizontalCenter: parent.right
            anchors.verticalCenter: parent.top
            iconSource: "qrc:///images/close.svg"
            opacity: (hovered || mouseArea.containsMouse) ? 1 : 0
            Behavior on opacity { NumberAnimation {}}
            onClicked: removeProject(index)
        }
    }



}
