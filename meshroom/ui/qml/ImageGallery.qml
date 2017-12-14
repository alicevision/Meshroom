import QtQuick 2.7
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import MaterialIcons 2.2
import "filepath.js" as Filepath
import QtQml.Models 2.2


/**
 * ImageGallery displays as a grid of Images a model containing Viewpoints objects.
 */
Panel {
    id: root

    property alias model: grid.model
    readonly property string currentItemSource: grid.currentItem ? grid.currentItem.source : ""
    signal removeImageRequest(var attribute)
    property int defaultCellSize: 160

    implicitWidth: 100
    implicitHeight: 300
    title: "Images"

    ColumnLayout {
        anchors.fill: parent

        GridView {
            id: grid

            Layout.fillWidth: true
            Layout.fillHeight: true

            cellWidth: thumbnailSizeSlider.value
            cellHeight: cellWidth
            ScrollBar.vertical: ScrollBar {}
            keyNavigationEnabled: true
            highlightFollowsCurrentItem: true
            focus: true
            clip: true


            delegate: Item {
                id: imageDelegate

                readonly property bool isCurrentItem: grid.currentIndex == index
                readonly property alias source: _viewpoint.source

                // retrieve viewpoints inner data
                QtObject {
                    id: _viewpoint
                    readonly property string source: object.value.get("path").value
                }

                width: grid.cellWidth
                height: grid.cellHeight

                MouseArea {
                    id: imageMA
                    anchors.fill: parent
                    anchors.margins: 6
                    hoverEnabled: true
                    acceptedButtons: Qt.LeftButton | Qt.RightButton
                    onPressed: {
                        onPressed: {
                           grid.currentIndex = index
                           if(mouse.button == Qt.RightButton)
                               imageMenu.popup()
                           else
                               grid.forceActiveFocus()
                       }
                    }
                    Menu {
                        id: imageMenu
                        MenuItem {
                            text: "Show Containing Folder"
                            onClicked: {
                                Qt.openUrlExternally(Filepath.dirname(imageDelegate.source))
                            }
                        }
                        MenuItem {
                            text: "Remove"
                            enabled: !root.readOnly
                            onClicked: removeImageRequest(object)
                        }
                    }

                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 0

                        // Image thumbnail and background
                        Rectangle {
                            id: imageBackground
                            color: Qt.darker(palette.base, 1.15)
                            Layout.fillHeight: true
                            Layout.fillWidth: true
                            border.color: grid.currentIndex == index ? palette.highlight : Qt.darker(palette.highlight)
                            border.width: imageMA.containsMouse || imageDelegate.isCurrentItem ? 2 : 0
                            Image {
                                anchors.fill: parent
                                anchors.margins: 4
                                source: imageDelegate.source
                                sourceSize: Qt.size(100, 100)
                                asynchronous: true
                                autoTransform: true
                                fillMode: Image.PreserveAspectFit
                            }
                        }
                        // Image basename
                        Label {
                            Layout.fillWidth: true
                            padding: 2
                            font.pointSize: 8
                            elide: Text.ElideMiddle
                            horizontalAlignment: Text.AlignHCenter
                            text: Filepath.basename(imageDelegate.source)
                            background: Rectangle {
                                color: imageDelegate.isCurrentItem ? palette.highlight : "transparent"
                            }
                        }
                    }
                }
            }

            // Explanatory placeholder when no image has been added yet
            Column {
                anchors.centerIn: parent
                visible: model.count == 0
                spacing: 4
                Label {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: MaterialIcons.photo_library
                    font.pointSize: 24
                    font.family: MaterialIcons.fontFamily
                }
                Label {
                    text: "Drop Image Files / Folders"
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
                // DropArea overlay
                Rectangle {
                    anchors.fill: parent
                    opacity: 0.4
                    visible: parent.containsDrag
                    color: palette.highlight
                }
            }
        }
    }

    footerContent: RowLayout {
        anchors.fill: parent

        // Image count
        Label {
            Layout.fillWidth: true
            text: model.count + " image" + (model.count > 1 ? "s" : "")
            elide: Text.ElideRight
        }

        // Thumbnail size icon and slider
        Label {
            text: MaterialIcons.photo_size_select_large
            font.family: MaterialIcons.fontFamily
            font.pixelSize: 13
        }
        Slider {
            id: thumbnailSizeSlider
            from: 70
            value: defaultCellSize
            to: 250
            implicitWidth: 70
            height: parent.height
        }
    }

}
