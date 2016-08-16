import QtQuick 2.7
import QtQuick.Layouts 1.3
import QtQuick.Controls 2.0

Item {

    implicitHeight: 30
    implicitWidth: parent ? parent.width : 200

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 10
        spacing: 0
        Label {
            text: currentScene.name
            state: "small"
        }
        Label {
            text: ".meshroom"
            state: "small"
            enabled: false
        }
        Label {
            text: "*"
            visible: currentScene.dirty
            state: "small"
        }
        Item { Layout.fillWidth: true } // spacer
        ToolButton {
            // iconSource: "qrc:///images/disk.svg"
            text: "SAVE"
            visible: currentScene.dirty
            onClicked: saveScene(null)
        }
        RowLayout {
            ProgressBar {
                indeterminate: true
            }
            ToolButton {
                // iconSource: "qrc:///images/pause.svg"
                text: "STOP"
                onClicked: currentScene.graph.stopWorker()
            }
            visible: currentScene.graph.isRunning
        }
    }

}
