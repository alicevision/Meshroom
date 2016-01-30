import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.2
import ".."
import "../controls"


Item {

    id: root

    property string title: "?"
    property string backgroundColor: Style.window.color.dark
    property Component content: null

    signal open()
    signal accept()
    signal reject()

    onOpen: visible = true
    onAccept: destroy()
    onReject: destroy()

    implicitWidth: parent.width
    implicitHeight: parent.height
    visible: false

    Rectangle {
        anchors.fill: parent
        color: Style.window.color.xdark
        opacity: 0.7
        Image {
            anchors.fill: parent
            source: "qrc:///images/stripes.png"
            fillMode: Image.Tile
            opacity: 0.3
        }
        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
        }
    }
    Item {
        anchors.centerIn: parent
        width: parent.width * 0.6
        height: parent.height * 0.6
        Rectangle {
            anchors.fill: parent
            color: root.backgroundColor
        }
        ColumnLayout {
            anchors.fill: parent
            spacing: 0
            RowLayout {
                width: parent.width
                height: 30
                Item {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 30
                    Text {
                        anchors.fill: parent
                        anchors.leftMargin: 10
                        text: root.title
                    }
                }
                ToolButton {
                    iconSource: "qrc:///images/close.svg"
                    onClicked: root.reject()
                }
            }
            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Loader {
                    anchors.fill: parent
                    anchors.margins: 20
                    sourceComponent: root.content
                }
            }
        }
    }
}
