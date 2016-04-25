import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0

Item {

    Rectangle {
        anchors.fill: parent
        anchors.margins: 5
        anchors.topMargin: 15
        color: mouseArea.containsMouse ? Style.window.color.selected : Style.window.color.xdark
        Behavior on color { ColorAnimation {} }
        MouseArea {
            id: mouseArea
            anchors.fill: parent
            hoverEnabled: true
            onClicked: selectScene(index)
        }
        ColumnLayout {
            anchors.fill: parent
            spacing: 0
            Item {
                Layout.fillWidth: true
                Layout.preferredHeight: width*3/4.0
                Text {
                    anchors.centerIn: parent
                    font.pixelSize: Style.text.size.small
                    color: Style.text.color.dark
                    text: "no preview"
                }
                Image {
                    anchors.fill: parent
                    anchors.margins: 4
                    source: _application.scenes.thumbnail
                    sourceSize: Qt.size(320, 320)
                    asynchronous: true
                    BusyIndicator {
                        anchors.centerIn: parent
                        running: parent.status === Image.Loading
                    }
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
            onClicked: removeScene(index)
        }
    }

}
