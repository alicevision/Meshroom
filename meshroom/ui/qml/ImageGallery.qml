import QtQuick 2.7
import QtQuick.Controls 2.3
import QtQuick.Controls 1.4 as Controls1 // For SplitView
import QtQuick.Layouts 1.3
import Qt.labs.platform 1.0 as Platform
import "Viewer" 1.0


Item {
    property alias model: grid.model
    implicitWidth: 300
    implicitHeight: 400

    clip: true

    SystemPalette {
        id: palette
    }

    Controls1.SplitView {
        anchors.fill: parent
        GridView {
            id: grid
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumWidth: cellWidth
            cellWidth: 160
            cellHeight: 120
            ScrollBar.vertical: ScrollBar {}
            keyNavigationEnabled: true
            highlightFollowsCurrentItem: true
            focus: true

            delegate: Item {
                property url source: object.value.get("path").value
                width: grid.cellWidth
                height: grid.cellHeight
                Image {
                    anchors.fill: parent
                    anchors.margins: 8
                    source:parent.source
                    sourceSize: Qt.size(150, 150)
                    asynchronous: true
                    autoTransform: true
                    fillMode: Image.PreserveAspectFit
                }
                Rectangle {
                   color: Qt.darker(palette.base, 1.15)
                   anchors.fill: parent
                   anchors.margins: 4
                   border.color: palette.highlight
                   border.width: imageMA.containsMouse || grid.currentIndex == index ? 2 : 0
                   z: -1

                   MouseArea {
                       id: imageMA
                       anchors.fill: parent
                       hoverEnabled: true
                       onClicked: {
                           grid.currentIndex = index
                           grid.forceActiveFocus()
                       }
                   }
                }
            }
            DropArea {
                id: dropArea
                anchors.fill: parent
                // TODO: onEntered: call specific method to filter files based on extension
                onDropped: {
                    _reconstruction.handleFilesDrop(drop)
                }
            }
        }

        Item {
            implicitWidth: Math.round(parent.width * 0.4)
            Layout.minimumWidth: 40
            Viewer2D {
                anchors.fill: parent
                anchors.margins: 4
                source: grid.currentItem.source
                Rectangle {
                    z: -1
                    anchors.fill: parent
                    color: Qt.darker(palette.base, 1.1)
                }
            }
        }
        Item {
            implicitWidth: Math.round(parent.width * 0.3)
            Layout.minimumWidth: 20
            Platform.FileDialog {
                id: modelDialog
                nameFilters: ["3D Models (*.obj)"]
                onAccepted: viewer3D.loadModel(file)
            }
            Viewer3D {
                id: viewer3D
                anchors.fill: parent
                Button {
                    text: "Load Model"
                    onClicked: modelDialog.open()
                }
            }
        }
    }
}
