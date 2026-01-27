// ImageGridView.qml

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQml.Models
import Qt.labs.qmlmodels

import Controls 1.0
import MaterialIcons 2.2
import Utils 1.0

GridView {
    id: grid

    // Exposed properties from parent - with default values
    property var m: null
    property var root: null
    property var searchBar: null
    property var thumbnailSizeSlider: null
    property var displayViewIdsAction: null
    property var intrinsicsFilterButton: null
    property var tempCameraInit: null
    property int centerViewId: 0
    property var errorDialog: null
    property var sortedModel: null
    
    // Signals
    signal removeImageRequest(var attribute)
    signal allViewpointsCleared()

    ScrollBar.vertical: MScrollBar {
        active: true
    }

    focus: true
    clip: true
    cellWidth: thumbnailSizeSlider ? thumbnailSizeSlider.value : 160
    cellHeight: cellWidth
    highlightFollowsCurrentItem: true
    keyNavigationEnabled: true
    property bool updateSelectedViewFromGrid: true

    // Update grid current item when selected view changes
    Connections {
        target: _reconstruction
        function onSelectedViewIdChanged() {
            if (_reconstruction.selectedViewId > -1) {
                grid.updateCurrentIndexFromSelectionViewId()
            }
        }
    }
    
    function makeCurrentItemVisible() {
        grid.positionViewAtIndex(grid.currentIndex, GridView.Visible)
    }

    function updateCurrentIndexFromSelectionViewId() {
        if (!sortedModel) return
        var idx = sortedModel.find(_reconstruction.selectedViewId, "viewId")
        if (idx >= 0 && grid.currentIndex !== idx) {
            grid.currentIndex = idx
        }
    }
    
    onCurrentItemChanged: {
        if (grid.updateSelectedViewFromGrid && grid.currentItem) {
            if (tempCameraInit !== null && grid.currentIndex == 0)
                _reconstruction.selectedViewId = -1
            _reconstruction.selectedViewId = grid.currentItem.viewpoint.get("viewId").value
        }
    }

    // Update grid item when corresponding thumbnail is computed
    Connections {
        target: ThumbnailCache
        function onThumbnailCreated(imgSource, callerID) {
            let item = grid.itemAtIndex(callerID);
            if (item && item.source === imgSource) {
                item.updateThumbnail()
                return
            }
            for (let idx = 0; idx < grid.count; idx++) {
                item = grid.itemAtIndex(idx)
                if (item && item.source === imgSource) {
                    item.updateThumbnail()
                }
            }
        }
    }

    model: sortedModel

    // Keyboard shortcut to change current image group
    Keys.priority: Keys.BeforeItem
    Keys.onPressed: function(event) {
        if (event.modifiers & Qt.AltModifier) {
            if (event.key === Qt.Key_Right && root && root.cameraInits) {
                _reconstruction.cameraInitIndex = Math.min(root.cameraInits.count - 1, root.cameraInitIndex + 1)
                event.accepted = true
            } else if (event.key === Qt.Key_Left) {
                _reconstruction.cameraInitIndex = Math.max(0, root.cameraInitIndex - 1)
                event.accepted = true
            }
        } else {
            if (event.key === Qt.Key_Right) {
                grid.moveCurrentIndexRight()
                event.accepted = true
            } else if (event.key === Qt.Key_Left) {
                grid.moveCurrentIndexLeft()
                event.accepted = true
            } else if (event.key === Qt.Key_Up) {
                grid.moveCurrentIndexUp()
                event.accepted = true
            } else if (event.key === Qt.Key_Down) {
                grid.moveCurrentIndexDown()
                event.accepted = true
            } else if (event.key === Qt.Key_Tab) {
                if (searchBar)
                    searchBar.forceActiveFocus()
                event.accepted = true
            }
        }
    }

    // Explanatory placeholder when no image has been added yet
    Column {
        id: dropImagePlaceholder
        anchors.centerIn: parent
        visible: (m && m.viewpoints ? m.viewpoints.count === 0 : true) && (!intrinsicsFilterButton || !intrinsicsFilterButton.checked)
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
    
    // Placeholder when the filtered images list is empty
    Column {
        id: noImageImagePlaceholder
        anchors.centerIn: parent
        visible: (m && m.viewpoints ? m.viewpoints.count !== 0 : false) && !dropImagePlaceholder.visible && grid.count === 0 && (!intrinsicsFilterButton || !intrinsicsFilterButton.checked)
        spacing: 4
        Label {
            anchors.horizontalCenter: parent.horizontalCenter
            text: MaterialIcons.filter_none
            font.pointSize: 24
            font.family: MaterialIcons.fontFamily
        }
        Label {
            text: "No images in this filtered view"
        }
    }

    DropArea {
        id: dropArea
        anchors.fill: parent
        enabled: m && !m.readOnly && (!intrinsicsFilterButton || !intrinsicsFilterButton.checked)
        keys: ["text/uri-list"]
        
        property int nbDraggedFiles: 0
        property var filesByType: ({})
        property int nbMeshroomScenes: 0
        
        onEntered: function(drag) {
            nbDraggedFiles = drag.urls.length
            filesByType = _reconstruction.getFilesByTypeFromDrop(drag.urls)
            nbMeshroomScenes = filesByType["meshroomScenes"].length
        }
        onDropped: function(drop) {
            if (nbMeshroomScenes == nbDraggedFiles || nbMeshroomScenes == 0) {
                if (root)
                    root.filesDropped(filesByType)
            } else {
                if (errorDialog)
                    errorDialog.open()
            }
        }

        // Background opacifier
        Rectangle {
            visible: dropArea.containsDrag
            anchors.fill: parent
            color: root ? root.palette.window : palette.window
            opacity: 0.8
        }

        Label {
            id: addArea
            anchors.fill: parent
            visible: dropArea.containsDrag
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            text: {
                if (dropArea.nbMeshroomScenes != dropArea.nbDraggedFiles && dropArea.nbMeshroomScenes != 0) {
                    return "Cannot Add Projects And Images Together"
                }

                if (dropArea.nbMeshroomScenes == 1 && dropArea.nbMeshroomScenes == dropArea.nbDraggedFiles) {
                    return "Load Project"
                } else if (dropArea.nbMeshroomScenes == dropArea.nbDraggedFiles) {
                    return "Only One Project"
                } else {
                    return "Add Images"
                }
            }
            font.bold: true
            background: Rectangle {
                color: dropArea.containsDrag ? parent.palette.highlight : parent.palette.window
                opacity: 0.8
                border.color: parent.palette.highlight
            }
        }
    }

    MouseArea {
        anchors.fill: parent
        onPressed: function(mouse) {
            if (mouse.button == Qt.LeftButton)
                grid.forceActiveFocus()
            mouse.accepted = false
        }
    }
}