import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQml.Models
import Qt.labs.qmlmodels

import Controls 1.0
import MaterialIcons 2.2
import Utils 1.0

ListView {
    id: root

    // Exposed properties from ImageGallery
    property var m: null
    property var gallery: null
    property var searchBar: null
    property var thumbnailSizeSlider: null
    property var intrinsicsFilterButton: null
    property var tempCameraInit: null
    property var errorDialog: null
    property var sortedModel: null

    property real cellHeight: thumbnailSizeSlider ? thumbnailSizeSlider.value / 2 : 80

    // Signals
    signal allViewpointsCleared()

    ScrollBar.vertical: MScrollBar {
        active: true
    }

    focus: true
    clip: true
    spacing: 2
    highlightFollowsCurrentItem: true
    keyNavigationEnabled: true
    highlightMoveDuration: 0

    // Update list current item when selected view changes
    Connections {
        target: _currentScene
        function onSelectedViewIdChanged() {
            if (_currentScene.selectedViewId > -1) {
                root.updateCurrentIndexFromSelectionViewId()
            }
        }
    }
    
    function makeCurrentItemVisible() {
        root.positionViewAtIndex(root.currentIndex, ListView.Visible)
    }

    function updateCurrentIndexFromSelectionViewId() {
        if (!sortedModel) return
        var idx = sortedModel.find(_currentScene.selectedViewId, "viewId")
        if (idx >= 0) {
            if (root.currentIndex !== idx) {
                root.currentIndex = idx
            }
            sortedModel.selectedIndex = idx
        }
    }
    
    onCurrentItemChanged: {
        if (root.currentItem) {
            if (tempCameraInit !== null && root.currentIndex == 0)
                _currentScene.selectedViewId = -1
            _currentScene.selectedViewId = root.currentItem.viewpoint.get("viewId").value
            if (sortedModel && sortedModel.selectedIndex !== root.currentIndex) {
                sortedModel.selectedIndex = root.currentIndex
                sortedModel.selectedIndices = [root.currentIndex]
            }
        } else {
            _currentScene.selectedViewId = "-1"
        }
    }

    // Update list item when corresponding thumbnail is computed
    Connections {
        target: ThumbnailCache
        function onThumbnailCreated(imgSource, callerID) {
            let item = root.itemAtIndex(callerID);
            if (item && item.source === imgSource) {
                item.updateThumbnail()
                return
            }
            for (let idx = 0; idx < root.count; idx++) {
                item = root.itemAtIndex(idx)
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
            if (event.key === Qt.Key_Right && gallery && gallery.cameraInits) {
                _currentScene.cameraInitIndex = Math.min(gallery.cameraInits.count - 1, gallery.cameraInitIndex + 1)
                event.accepted = true
            } else if (event.key === Qt.Key_Left) {
                _currentScene.cameraInitIndex = Math.max(0, gallery.cameraInitIndex - 1)
                event.accepted = true
            }
        } else {
            if (event.key === Qt.Key_Down) {
                root.incrementCurrentIndex()
                event.accepted = true
            } else if (event.key === Qt.Key_Up) {
                root.decrementCurrentIndex()
                event.accepted = true
            } else if (event.key === Qt.Key_Tab) {
                if (searchBar)
                    searchBar.forceActiveFocus()
                event.accepted = true
            } else if (event.key === Qt.Key_Escape) {
                if (sortedModel)
                    sortedModel.selectedIndices = [sortedModel.selectedIndex]
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
        visible: (m && m.viewpoints ? m.viewpoints.count !== 0 : false) && !dropImagePlaceholder.visible && root.count === 0 && (!intrinsicsFilterButton || !intrinsicsFilterButton.checked)
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
            filesByType = _currentScene.getFilesByTypeFromDrop(drag.urls)
            nbMeshroomScenes = filesByType["meshroomScenes"].length
        }
        onDropped: function(drop) {
            if (nbMeshroomScenes == nbDraggedFiles || nbMeshroomScenes == 0) {
                if (gallery)
                    gallery.filesDropped(filesByType)
            } else {
                if (errorDialog)
                    errorDialog.open()
            }
        }

        // Background opacifier
        Rectangle {
            visible: dropArea.containsDrag
            anchors.fill: parent
            color: gallery ? gallery.palette.window : palette.window
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
                root.forceActiveFocus()
            mouse.accepted = false
        }
    }
}