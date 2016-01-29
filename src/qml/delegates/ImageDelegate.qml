import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0

Item {
    width: ListView.view ? ListView.view.width : 0
    height: 30
    clip: true
    signal imageSelected(string url)
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        anchors.margins: 2
        cursorShape: Qt.PointingHandCursor
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        onClicked: imageSelected(model.url)
    }
    Rectangle {
        anchors.fill: parent
        color: {
            if(mouseArea.containsMouse)
                return Style.window.color.xlight;
            return Style.window.color.dark;
        }
        opacity: 0.2
    }
    RowLayout {
        anchors.fill: parent
        spacing: 0
        Rectangle {
            Layout.fillHeight: true
            Layout.preferredWidth: Math.min(parent.height*4/3.0, parent.width*0.4)
            color: "black"
            Image {
                anchors.fill: parent
                source: model.url
                fillMode: Image.PreserveAspectFit
                asynchronous: true
            }
        }
        Text {
            text: model.name
        }
    }
}
