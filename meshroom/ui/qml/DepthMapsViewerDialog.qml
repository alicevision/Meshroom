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
    width: 1200
    y: parent.height / 2 - height / 2
    height: 700

    // Fade in transition
    enter: Transition {
        NumberAnimation { property: "opacity"; from: 0.0; to: 1.0 }
    }

    modal: true
    closePolicy: Dialog.CloseOnEscape | Dialog.CloseOnPressOutside
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

    RowLayout {
        width: parent.width
        height: parent.height
        spacing: 6

        Row {
            Layout.fillWidth: true
            Layout.fillHeight: true

            ImageListViewer {
                id: imageListViewer

                // Update images list when node is double clicked
                Connections {
                    target: root
                    onNodeChanged: { imageListViewer.imgs = root.node.searchForFiles(".exr") }
                }
            }
        }

        Row {
            Layout.fillWidth: true
            Layout.fillHeight: true

            Viewer2D {
                id: viewer2D
                height: 200
                width: 200
                anchors.fill: parent
                source: imageListViewer.currentImg
            }

            Button {
                text: "Add To 3D Scene"

                onClicked: {
                    root.viewIn3D(imageListViewer.currentImg)
                }
            }
        }
    }
}
