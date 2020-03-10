import QtQuick 2.7
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import MaterialIcons 2.2
import QtQml.Models 2.2

import Controls 1.0
import Utils 1.0

/**
 * ImageGallery displays as a grid of Images a model containing Viewpoints objects.
 * It manages a model of multiple CameraInit nodes as individual groups.
 */
Panel {
    id: root

    property variant cameraInits
    property variant cameraInit
    property variant hdrCameraInit
    readonly property alias currentItem: grid.currentItem
    readonly property string currentItemSource: grid.currentItem ? grid.currentItem.source : ""
    readonly property var currentItemMetadata: grid.currentItem ? grid.currentItem.metadata : undefined
    property int defaultCellSize: 160
    property int currentIndex: 0
    property bool readOnly: false

    signal removeImageRequest(var attribute)
    signal filesDropped(var drop, var augmentSfm)

    title: "Images"
    implicitWidth: (root.defaultCellSize + 2) * 2

    function changeCurrentIndex(newIndex) {
        _reconstruction.cameraInitIndex = newIndex
    }

    QtObject {
        id: m
        property variant currentCameraInit: displayHDR.checked ? _reconstruction.hdrCameraInit : root.cameraInit
        property variant viewpoints: currentCameraInit ? currentCameraInit.attribute('viewpoints').value : undefined
        property bool readOnly: root.readOnly || displayHDR.checked
    }

    headerBar: RowLayout {
        MaterialToolButton {
            text: MaterialIcons.more_vert
            font.pointSize: 11
            padding: 2
            checkable: true
            checked: galleryMenu.visible
            onClicked: galleryMenu.open()
            Menu {
                id: galleryMenu
                y: parent.height
                x: -width + parent.width
                MenuItem {
                    text: "Edit Sensor Database..."
                    onTriggered: {
                        sensorDBDialog.open()
                    }
                }

                Menu {
                    title: "Advanced"
                    Action {
                        id: displayViewIdsAction
                        text: "Display View IDs"
                        checkable: true
                    }
                }
            }
        }
    }

    SensorDBDialog {
        id: sensorDBDialog
        sensorDatabase: Filepath.stringToUrl(cameraInit.attribute("sensorDatabase").value)
        readOnly: _reconstruction.computing
        onUpdateIntrinsicsRequest: _reconstruction.rebuildIntrinsics(cameraInit)
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 4

        GridView {
            id: grid

            Layout.fillWidth: true
            Layout.fillHeight: true

            ScrollBar.vertical: ScrollBar { minimumSize: 0.05 }

            focus: true
            clip: true
            cellWidth: thumbnailSizeSlider.value
            cellHeight: cellWidth
            highlightFollowsCurrentItem: true
            keyNavigationEnabled: true

            // Update grid current item when selected view changes
            Connections {
                target: _reconstruction
                onSelectedViewIdChanged: {
                    var idx = grid.model.find(_reconstruction.selectedViewId, "viewId")
                    if(idx >= 0)
                        grid.currentIndex = idx
                }
            }

            model: SortFilterDelegateModel {
                id: sortedModel
                model: m.viewpoints
                sortRole: "path"
                // TODO: provide filtering on reconstruction status
                // filterRole: _reconstruction.sfmReport ? "reconstructed" : ""
                // filterValue: true / false
                // in modelData:
                // if(filterRole == roleName)
                //     return _reconstruction.isReconstructed(item.model.object)

                // override modelData to return basename of viewpoint's path for sorting
                function modelData(item, roleName) {
                    var value = item.model.object.childAttribute(roleName).value
                    if(roleName == sortRole)
                        return Filepath.basename(value)
                    else
                        return value
                }

                delegate: ImageDelegate {
                    id: imageDelegate

                    viewpoint: object.value
                    width: grid.cellWidth
                    height: grid.cellHeight
                    readOnly: m.readOnly
                    displayViewId: displayViewIdsAction.checked

                    isCurrentItem: GridView.isCurrentItem

                    onIsCurrentItemChanged: {
                        if(isCurrentItem)
                            _reconstruction.selectedViewId = viewpoint.get("viewId").value
                    }

                    onPressed: {
                        grid.currentIndex = DelegateModel.filteredIndex
                        if(mouse.button == Qt.LeftButton)
                            grid.forceActiveFocus()
                    }

                    function sendRemoveRequest()
                    {
                        if(!readOnly)
                            removeImageRequest(object)
                    }

                    onRemoveRequest: sendRemoveRequest()
                    Keys.onDeletePressed: sendRemoveRequest()

                    RowLayout {
                        anchors.top: parent.top
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.margins: 2
                        spacing: 2

                        property bool valid: Qt.isQtObject(object) // object can be evaluated to null at some point during creation/deletion
                        property bool inViews: valid && _reconstruction.sfmReport && _reconstruction.isInViews(object)

                        // Camera Initialization indicator
                        IntrinsicsIndicator {
                            intrinsic: parent.valid ? _reconstruction.getIntrinsic(object) : null
                            metadata: imageDelegate.metadata
                        }

                        // Rig indicator
                        Loader {
                            id: rigIndicator
                            property int rigId: parent.valid ? object.childAttribute("rigId").value : -1
                            active: rigId >= 0
                            sourceComponent: ImageBadge {
                                property int rigSubPoseId: model.object.childAttribute("subPoseId").value
                                text: MaterialIcons.link
                                ToolTip.text: "<b>Rig: Initialized</b><br>" +
                                              "Rig ID: " + rigIndicator.rigId + " <br>" +
                                              "SubPose: " + rigSubPoseId
                            }
                        }

                        Item { Layout.fillWidth: true }

                        // Reconstruction status indicator
                        Loader {
                            active: parent.inViews
                            visible: active
                            sourceComponent: ImageBadge {
                                property bool reconstructed: _reconstruction.sfmReport && _reconstruction.isReconstructed(model.object)
                                text: reconstructed ? MaterialIcons.videocam : MaterialIcons.videocam_off
                                color: reconstructed ? Colors.green : Colors.red
                                ToolTip.text: "<b>Camera: " + (reconstructed ? "" : "Not ") + "Reconstructed</b>"
                            }
                        }
                    }
                }
            }

            // Keyboard shortcut to change current image group
            Keys.priority: Keys.BeforeItem
            Keys.onPressed: {
                if(event.modifiers & Qt.AltModifier)
                {
                    event.accepted = true
                    if(event.key == Qt.Key_Right)
                        root.changeCurrentIndex(Math.min(root.cameraInits.count - 1, root.currentIndex + 1))
                    else if(event.key == Qt.Key_Left)
                        root.changeCurrentIndex(Math.max(0, root.currentIndex - 1))
                }
            }

            // Explanatory placeholder when no image has been added yet
            Column {
                anchors.centerIn: parent
                visible: grid.model.count == 0
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
                enabled: !m.readOnly
                keys: ["text/uri-list"]
                // TODO: onEntered: call specific method to filter files based on extension
                onDropped: {
                    var augmentSfm = augmentArea.hovered
                    root.filesDropped(drop, augmentSfm)
                }

                // Background opacifier
                Rectangle {
                    visible: dropArea.containsDrag
                    anchors.fill: parent
                    color: root.palette.window
                    opacity: 0.8
                }

                ColumnLayout {
                    anchors.fill: parent
                    visible: dropArea.containsDrag
                    spacing: 1
                    Label {
                        id: addArea
                        property bool hovered: dropArea.drag.y < height
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        text: "Add Images"
                        font.bold: true
                        background: Rectangle {
                            color: parent.hovered ? parent.palette.highlight : parent.palette.window
                            opacity: 0.8
                            border.color: parent.palette.highlight
                        }
                    }

                    // DropArea overlay
                    Label {
                        id: augmentArea
                        property bool hovered: visible && dropArea.drag.y >= y
                        Layout.fillWidth: true
                        Layout.preferredHeight: parent.height * 0.3
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        text: "Augment Reconstruction"
                        font.bold: true
                        wrapMode: Text.WrapAtWordBoundaryOrAnywhere
                        visible: m.viewpoints ? m.viewpoints.count > 0 : false
                        background: Rectangle {
                            color: parent.hovered ? palette.highlight : palette.window
                            opacity: 0.8
                            border.color: parent.palette.highlight
                        }
                    }
                }
            }
        }

        RowLayout {
            Layout.fillHeight: false
            visible: root.cameraInits.count > 1
            Layout.alignment: Qt.AlignHCenter
            spacing: 2

            ToolButton {
                text: MaterialIcons.navigate_before
                font.family: MaterialIcons.fontFamily
                ToolTip.text: "Previous Group (Alt+Left)"
                ToolTip.visible: hovered
                enabled: nodesCB.currentIndex > 0
                onClicked: nodesCB.decrementCurrentIndex()
            }
            Label { id: groupLabel; text: "Group " }
            ComboBox {
                id: nodesCB
                model: root.cameraInits.count
                implicitWidth: 40
                currentIndex: root.currentIndex
                onActivated: root.changeCurrentIndex(currentIndex)
            }
            Label { text: "/ " + (root.cameraInits.count - 1) }
            ToolButton {
                text: MaterialIcons.navigate_next
                font.family: MaterialIcons.fontFamily
                ToolTip.text: "Next Group (Alt+Right)"
                ToolTip.visible: hovered
                enabled: root.currentIndex < root.cameraInits.count - 1
                onClicked: nodesCB.incrementCurrentIndex()
            }
        }
    }

    footerContent: RowLayout {

        // Image count
        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            RowLayout {
                MaterialLabel { text: MaterialIcons.image }
                Label { text: grid.model.count }
            }
            RowLayout {
                visible: _reconstruction.cameraInit && _reconstruction.nbCameras
                MaterialLabel { text: MaterialIcons.videocam }
                Label { text: _reconstruction.cameraInit ? _reconstruction.nbCameras : 0 }
            }
        }

        MaterialToolButton {
            id: displayHDR
            font.pointSize: 20
            padding: 0
            anchors.margins: 0
            implicitHeight: 14
            ToolTip.text: "Visualize HDR images"
            text: MaterialIcons.hdr_on
            visible: _reconstruction.ldr2hdr
            enabled: visible && _reconstruction.ldr2hdr.isComputed()
            onEnabledChanged: {
                // Reset the toggle to avoid getting stuck
                // with the HDR node checked but disabled.
                checked = false;
            }
            checkable: true
            checked: false
            onClicked: { _reconstruction.setupLDRToHDRCameraInit(); }
        }

        Item { Layout.fillHeight: true; Layout.fillWidth: true }

        // Thumbnail size icon and slider
        MaterialToolButton {
            text: MaterialIcons.photo_size_select_large
            padding: 0
            anchors.margins: 0
            font.pointSize: 11
            onClicked: { thumbnailSizeSlider.value = defaultCellSize; }
        }
        Slider {
            id: thumbnailSizeSlider
            from: 70
            value: defaultCellSize
            to: 250
            implicitWidth: 70
        }
    }

}
