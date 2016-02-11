import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0

Item {
    width: ListView.view ? ListView.view.width : 0
    height: ListView.view ? ListView.view.height : 0
    Rectangle {
        anchors.fill: parent
        color: "black"
        Image {
            anchors.fill: parent
            source: model.exists ? model.url : ""
            fillMode: Image.PreserveAspectFit
            asynchronous: true
            BusyIndicator {
                anchors.centerIn: parent
                running: parent.status === Image.Loading
            }
            Rectangle {
                anchors.fill: parent
                visible: !root.editable
                color: "black"
                opacity: 0.6
            }
        }
    }
}
