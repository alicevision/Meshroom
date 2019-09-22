import QtQuick 2.9
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import Utils 1.0
import Controls 1.0
import MaterialIcons 2.2
import Viewer 1.0


/// Meshroom "Depth Maps" window
Dialog {
    id: root

    property var node
    property var viewIn3D

    x: parent.width / 2 - width / 2
    y: parent.height / 2 - height / 2
    width: parent.width / 1.5
    height: parent.height / 1.5

    // Fade in transition
    enter: Transition {
        NumberAnimation { property: "opacity"; from: 0.0; to: 1.0 }
    }

    modal: true
    closePolicy: Dialog.CloseOnEscape
    padding: 30

    header: Pane {
        background: Item {}
        MaterialToolButton {
            text: MaterialIcons.close
            anchors.right: parent.right
            onClicked: root.close()
        }
        Label {
            text: "Depth Maps"
        }
    }

    Row {
        width: parent.width/4
        height: parent.height

        Column {
            width: parent.width
            height: parent.height
            
            MaterialToolButton {
                text: MaterialIcons.refresh
                ToolTip.text: "Reload"
                onClicked: { fileList.files = root.node.searchForFiles(".exr") }
            }

            FileList {
                id: fileList

                width: parent.width
                height: parent.height-20

                // Update images list when node is double clicked
                Connections {
                    target: root
                    onNodeChanged: { fileList.files = root.node.searchForFiles(".exr") }
                }
            }
        }
    }

    Row {
        width: parent.width/(4/3)
        height: parent.height
        anchors.right: parent.right

        Column {
            width: parent.width
            height: parent.height-20

            Viewer2D {
                id: viewer2D
                anchors.fill: parent
                source: fileList.currentFile

                Rectangle {
                    z: -1
                    anchors.fill: parent
                    color: Qt.darker(activePalette.base, 1.1)
                }
            }

            Button {
                text: "Add To 3D Scene"

                anchors.top: viewer2D.bottom
                anchors.right: parent.right

                onClicked: {
                    root.viewIn3D(fileList.currentFile)
                }
            }
        }
    }
}
