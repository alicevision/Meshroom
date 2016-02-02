import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0
import "menuPage"
import "../../delegates"

Rectangle {

    color: Style.window.color.normal

    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        MenuHeader {
            Layout.fillWidth: true
            Layout.preferredHeight: 30
        }
        ScrollView {
            id: scrollview
            Layout.fillWidth: true
            Layout.fillHeight: true
            ColumnLayout {
                width: scrollview.width
                height: listview.contentHeight + mouseContainer.height
                spacing: 0
                ListView {
                    id: listview
                    Layout.fillWidth: true
                    Layout.preferredHeight: contentHeight
                    model: currentProject.proxy
                    delegate: JobDelegate { height: 80; width: parent.width }
                    spacing: 1
                    interactive: false
                }
                MouseArea {
                    id: mouseContainer
                    Layout.fillWidth: true
                    Layout.preferredHeight: 50
                    hoverEnabled: true
                    onClicked: duplicateJob()
                    Rectangle {
                        anchors.fill: parent
                        anchors.topMargin: 1
                        color: Style.window.color.xdark
                        opacity: mouseContainer.containsMouse ? 0.8 : 0.4
                        Behavior on opacity { NumberAnimation {} }
                        Image {
                            anchors.centerIn: parent
                            sourceSize: Qt.size(25, 25)
                            source: "qrc:///images/plus.svg"
                            asynchronous: true
                        }
                    }
                }
            }
        }
    }

}
