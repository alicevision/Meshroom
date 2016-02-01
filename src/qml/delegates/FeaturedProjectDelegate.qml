import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0

Item {

    Rectangle {
        anchors.fill: parent
        color: mouseArea.containsMouse ? Style.window.color.selected : Style.window.color.xdark
        Behavior on color { ColorAnimation {} }
        MouseArea {
            id: mouseArea
            anchors.fill: parent
            hoverEnabled: true
            onClicked: addProject(model.url)
        }
        RowLayout {
            anchors.fill: parent
            spacing: 0
            ToolButton {
                iconSource: "qrc:///images/arrow.svg"
            }
            Text {
                Layout.fillWidth: true
                Layout.fillHeight: true
                text: model.url.toString().replace("file://","")
            }
        }
    }



}
