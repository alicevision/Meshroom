import QtQuick 2.7
import QtQuick.Controls 2.3
import QtQuick.Controls 1.4 as Controls1 // For SplitView
import QtQuick.Layouts 1.3
import Qt.labs.platform 1.0 as Platform
import "Viewer" 1.0


Item {
    id: root

    property alias model: grid.model
    property bool readOnly: false
    property string meshFile: ''
    implicitWidth: 300
    implicitHeight: 400

    signal removeImageRequest(var attribute)
    onMeshFileChanged: viewer3D.clear()

    SystemPalette {
        id: palette
    }

    function dirname(filename) {
        return filename.substring(0, filename.lastIndexOf('/'))
    }

    Controls1.SplitView {
        anchors.fill: parent
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumWidth: grid.cellWidth

            GridView {
                id: grid
                Layout.fillWidth: true
                Layout.fillHeight: true

                cellWidth: thumbnailSizeSlider.value
                cellHeight: cellWidth * 0.75
                ScrollBar.vertical: ScrollBar {}
                keyNavigationEnabled: true
                highlightFollowsCurrentItem: true
                focus: true
                clip: true

                delegate: Item {
                    id: imageDelegate
                    property string source: object.value.get("path").value
                    width: grid.cellWidth
                    height: grid.cellHeight
                    Image {
                        anchors.fill: parent
                        anchors.margins: 8
                        source:parent.source
                        sourceSize: Qt.size(100, 100)
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
                           acceptedButtons: Qt.LeftButton | Qt.RightButton
                           onPressed: {
                               grid.currentIndex = index
                               if(mouse.button == Qt.RightButton)
                                   imageMenu.popup()
                               else
                                   grid.forceActiveFocus()
                           }
                       }
                    }
                    Menu {
                        id: imageMenu
                        MenuItem {
                            text: "Show Containing Folder"
                            onClicked: {
                                Qt.openUrlExternally(dirname(imageDelegate.source))
                            }
                        }

                        MenuItem {
                            text: "Remove"
                            enabled: !root.readOnly
                            onClicked: removeImageRequest(object)
                        }
                    }
                }
                DropArea {
                    id: dropArea
                    anchors.fill: parent
                    enabled: !root.readOnly
                    // TODO: onEntered: call specific method to filter files based on extension
                    onDropped: {
                        _reconstruction.handleFilesDrop(drop)
                    }
                }
            }
            Pane {
                Layout.fillWidth: true
                padding: 2
                background: Rectangle { color: Qt.darker(palette.window, 1.15) }
                RowLayout {
                    width: parent.width
                    Label {
                        Layout.fillWidth: true
                        text: model.count + " image" + (model.count > 1 ? "s" : "")
                        padding: 4
                    }
                    Slider {
                        id: thumbnailSizeSlider
                        from: 70
                        value: 160
                        to: 250
                        implicitWidth: 70
                        Layout.margins: 2
                    }
                }
            }
        }

        Item {
            implicitWidth: Math.round(parent.width * 0.4)
            Layout.minimumWidth: 40
            Viewer2D {
                anchors.fill: parent
                anchors.margins: 2
                source: grid.count && grid.currentItem ? grid.currentItem.source : ''
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

            Viewer3D {
                id: viewer3D
                anchors.fill: parent
                DropArea {
                    anchors.fill: parent
                    onDropped: viewer3D.source = drop.urls[0]
                }
            }

            Label {
                anchors.centerIn: parent
                text: "Loading Model..."
                visible: viewer3D.loading
                padding: 6
                background: Rectangle { color: palette.base; opacity: 0.5 }
            }

            Label {
                text: "3D Model not available"
                visible: meshFile == ''
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 10
                anchors.horizontalCenter: parent.horizontalCenter
                padding: 6
                background: Rectangle { color: palette.base; opacity: 0.5 }
            }

            // Load reconstructed model
            Button {
                text: "Load Model"
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 10
                anchors.horizontalCenter: parent.horizontalCenter
                visible: meshFile != '' && (viewer3D.source != meshFile)
                onClicked: viewer3D.source = meshFile
            }
        }
    }
}
