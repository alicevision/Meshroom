import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import MaterialIcons 2.2
import Utils 1.0

/**
 * ImageDelegate for a Viewpoint object.
 */

Item {
    id: root

    property variant viewpoint
    property int cellID: -1
    property alias source: _viewpoint.source
    property alias metadata: _viewpoint.metadata
    property bool readOnly: false
    property bool displayViewId: false
    property bool displayThumbnail: true
    property int layoutMode: 0  // 0: grid, 1: list

    property variant parentModel
    property int selectedIndex: parentModel ? parentModel.selectedIndex : -1
    property bool isCurrentItem: cellID >= 0 && cellID === selectedIndex
    property var selectedIndices: parentModel ? parentModel.selectedIndices : []
    property bool isInMultiSelection: cellID >= 0 && selectedIndices.indexOf(cellID) >= 0

    signal pressed(var mouse)
    signal removeSelectedRequest()
    signal removeAllImagesRequest()

    default property alias children: imageMA.children

    // Internal properties to hold thumbnail source & loading status
    property url thumbnailSource: ""
    property int thumbnailStatus: Image.Null
    property int retryCount: 0

    // Retrieve viewpoints inner data
    QtObject {
        id: _viewpoint
        property url source: viewpoint ? Filepath.stringToUrl(viewpoint.get("path").value) : ''
        property int viewId: viewpoint ? viewpoint.get("viewId").value : -1
        property string metadataStr: viewpoint ? viewpoint.get("metadata").value : ''
        property var metadata: metadataStr ? JSON.parse(viewpoint.get("metadata").value) : {}
    }

    // Update thumbnail location
    // Can be called from the GridView when a new thumbnail has been written on disk
    function updateThumbnail() {
        if (!displayThumbnail) return
        root.thumbnailSource = ThumbnailCache.thumbnail(root.source, root.cellID)
    }
    onSourceChanged: {
        root.retryCount = 0
        updateThumbnail()
    }
    onDisplayThumbnailChanged: {
        if (displayThumbnail) {
            root.retryCount = 0
            updateThumbnail()
        } else {
            root.thumbnailSource = ""
        }
    }

    // Periodically retry loading the thumbnail until it is available or max retries is reached.
    // This acts as a safety net in case the thumbnailCreated signal emitted from the background
    // thread is not properly delivered to QML.
    Timer {
        id: retryTimer
        interval: 2000
        repeat: true
        running: root.displayThumbnail
                 && root.thumbnailStatus !== Image.Ready
                 && root.thumbnailStatus !== Image.Error
                 && root.retryCount < 15
        onTriggered: {
            root.retryCount++
            updateThumbnail()
        }
    }

    MouseArea {
        id: imageMA
        anchors.fill: parent
        anchors.margins: 6
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        onPressed: function(mouse) {
            if (mouse.button == Qt.RightButton)
                imageMenu.popup()
            root.pressed(mouse)
        }

        Menu {
            id: imageMenu
            MenuItem {
                text: "Show Containing Folder"
                onClicked: {
                    Qt.openUrlExternally(Filepath.dirname(root.source))
                }
            }
            MenuItem {
                text: "Remove Selected Image" + (root.selectedIndices.length > 1 ? "s " : " ") + "(" + root.selectedIndices.length + ")"
                enabled: !root.readOnly && root.selectedIndices.length > 0
                onClicked: removeSelectedRequest()
            }
            MenuItem {
                text: "Remove All Images"
                enabled: !root.readOnly
                onClicked: removeAllImagesRequest()
            }
            MenuItem {
                text: "Define As Center Image"
                property var activeNode: _currentScene ? _currentScene.activeNodes.get("SfMTransform").node : null
                enabled: !root.readOnly && _viewpoint.viewId != -1 && _currentScene && activeNode
                onClicked: _currentScene.setAttribute(activeNode.attribute("transformation"), _viewpoint.viewId.toString())
            }
            Menu {
                id: sfmSetPairMenu
                title: "SfM: Define Initial Pair"
                property var activeNode: _currentScene ? _currentScene.activeNodes.get("StructureFromMotion").node : null
                enabled: !root.readOnly && _viewpoint.viewId != -1 && _currentScene && activeNode

                MenuItem {
                    text: "A"
                    onClicked: _currentScene.setAttribute(sfmSetPairMenu.activeNode.attribute("initialPairA"), _viewpoint.viewId.toString())
                }

                MenuItem {
                    text: "B"
                    onClicked: _currentScene.setAttribute(sfmSetPairMenu.activeNode.attribute("initialPairB"), _viewpoint.viewId.toString())
                }
            }
        }

        // Switch from the grid component (column layout) to the list component (row layout)
        Loader {
            id: itemDelegate
            anchors.fill: parent
            sourceComponent: root.layoutMode === 0 ? gridDelegate : listDelegate
        }

        Component {
            id: gridDelegate
            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                // Image thumbnail and background
                Rectangle {
                    color: Qt.darker(grid_imageLabel.palette.base, 1.15)
                    Layout.fillHeight: true
                    Layout.fillWidth: true
                    visible: root.displayThumbnail
                    border.color: isCurrentItem ? grid_imageLabel.palette.highlight : Qt.darker(grid_imageLabel.palette.highlight)
                    border.width: imageMA.containsMouse || root.isCurrentItem || root.isInMultiSelection ? 2 : 0
                    Image {
                        id: grid_thumbnail
                        anchors.fill: parent
                        anchors.margins: 4
                        source: root.thumbnailSource
                        asynchronous: true
                        autoTransform: true
                        fillMode: Image.PreserveAspectFit
                        smooth: false
                        cache: false
                        onStatusChanged: root.thumbnailStatus = status
                    }
                    BusyIndicator {
                        anchors.centerIn: parent
                        running: grid_thumbnail.status === Image.Loading
                                 || (grid_thumbnail.status === Image.Null
                                     && root.thumbnailSource == ""
                                     && retryTimer.running)
                    }
                    MaterialLabel {
                        anchors.centerIn: parent
                        visible: grid_thumbnail.status === Image.Error
                        text: MaterialIcons.image_not_supported
                        font.pointSize: 20
                    }
                }

                // Placeholder icon shown when thumbnails are disabled
                Label {
                    Layout.fillHeight: true
                    Layout.fillWidth: true
                    visible: !root.displayThumbnail
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    text: MaterialIcons.image
                    font.family: MaterialIcons.fontFamily
                    font.pointSize: 16
                    color: palette.mid
                }

                // Image basename
                Label {
                    id: grid_imageLabel
                    Layout.fillWidth: true
                    padding: 2
                    font.pointSize: 8
                    elide: Text.ElideMiddle
                    horizontalAlignment: Text.AlignHCenter
                    text: Filepath.basename(root.source)
                    background: Rectangle {
                        color: root.isCurrentItem ? parent.palette.highlight : (root.isInMultiSelection ? Qt.alpha(parent.palette.highlight, 0.5) : "transparent")
                    }
                }

                // Image viewId
                Loader {
                    active: displayViewId
                    Layout.fillWidth: true
                    visible: active
                    sourceComponent: Label {
                        padding: grid_imageLabel.padding
                        font.pointSize: grid_imageLabel.font.pointSize
                        elide: grid_imageLabel.elide
                        horizontalAlignment: grid_imageLabel.horizontalAlignment
                        text: _viewpoint.viewId
                        background: Rectangle {
                            color: grid_imageLabel.background.color
                        }
                    }
                }
            }
        }

        Component {
            id: listDelegate
            RowLayout {
                anchors.fill: parent
                spacing: 4

                // Image thumbnail and background
                Rectangle {
                    color: Qt.darker(list_imageLabel.palette.base, 1.15)
                    Layout.fillHeight: true
                    Layout.preferredWidth: 100
                    visible: root.displayThumbnail
                    
                    border.color: isCurrentItem ? list_imageLabel.palette.highlight : Qt.darker(list_imageLabel.palette.highlight)
                    border.width: imageMA.containsMouse || root.isCurrentItem || root.isInMultiSelection ? 2 : 0

                    Image {
                        id: list_thumbnail
                        anchors.fill: parent
                        anchors.margins: 4
                        source: root.thumbnailSource
                        asynchronous: true
                        autoTransform: true
                        fillMode: Image.PreserveAspectFit
                        smooth: false
                        cache: false
                        onStatusChanged: root.thumbnailStatus = status
                    }
                    BusyIndicator {
                        anchors.centerIn: parent
                        running: list_thumbnail.status === Image.Loading
                                 || (list_thumbnail.status === Image.Null
                                     && root.thumbnailSource == ""
                                     && retryTimer.running)
                    }
                    MaterialLabel {
                        anchors.centerIn: parent
                        visible: list_thumbnail.status === Image.Error
                        text: MaterialIcons.image_not_supported
                        font.pointSize: 20
                    }
                }

                // Placeholder icon shown when thumbnails are disabled
                Label {
                    Layout.fillHeight: true
                    visible: !root.displayThumbnail
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    text: MaterialIcons.image
                    font.family: MaterialIcons.fontFamily
                    font.pointSize: 14
                    color: palette.mid
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 0

                    // Image basename
                    Label {
                        id: list_imageLabel
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        padding: 4
                        font.pointSize: 8
                        elide: Text.ElideMiddle
                        horizontalAlignment: Text.AlignLeft
                        verticalAlignment: Text.AlignVCenter
                        text: Filepath.basename(root.source)
                        background: Rectangle {
                            color: root.isCurrentItem ? parent.palette.highlight : (root.isInMultiSelection ? Qt.alpha(parent.palette.highlight, 0.5) : "transparent")
                        }
                    }

                    // Image viewId
                    Loader {
                        active: root.displayViewId
                        Layout.fillWidth: true
                        Layout.fillHeight: active
                        visible: active
                        sourceComponent: Label {
                            padding: list_imageLabel.padding
                            font.pointSize: list_imageLabel.font.pointSize
                            elide: list_imageLabel.elide
                            horizontalAlignment: list_imageLabel.horizontalAlignment
                            verticalAlignment: list_imageLabel.verticalAlignment
                            text: _viewpoint.viewId
                            background: Rectangle {
                                color: list_imageLabel.background.color
                            }
                        }
                    }
                }
            }
        }
    }
}