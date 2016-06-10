import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0

Rectangle {

    color: Style.window.color.xdark

    RowLayout {
        anchors.fill: parent
        spacing: 0
        Item { Layout.preferredWidth: 10 } // spacer
        Text {
            text: currentScene.name
            font.pixelSize: Style.text.size.small
        }
        Text {
            text: ".meshroom"
            color: Style.text.color.dark
            font.pixelSize: Style.text.size.small
        }
        Text {
            text: "*"
            color: Style.text.color.dark
            font.pixelSize: Style.text.size.small
            visible: currentScene.dirty
        }
        Item { Layout.fillWidth: true } // spacer
        ToolButton {
            iconSource: "qrc:///images/disk.svg"
            text: "SAVE"
            visible: currentScene.dirty
            onClicked: saveScene(null)
        }
        RowLayout {
            ProgressBar {
                indeterminate: true
            }
            ToolButton {
                iconSource: "qrc:///images/pause.svg"
                text: "STOP"
                onClicked: currentScene.graph.abort()
            }
            visible: currentScene.graph.running
        }
    }

}
