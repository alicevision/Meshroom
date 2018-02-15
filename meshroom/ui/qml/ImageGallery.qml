import QtQuick 2.7
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import MaterialIcons 2.2
import QtQml.Models 2.2


/**
 * ImageGallery displays as a grid of Images a model containing Viewpoints objects.
 * It manages a model of multiple CameraInit nodes as individual groups.
 */
Panel {
    id: root

    property variant cameraInits
    property variant cameraInit
    readonly property alias currentItem: grid.currentItem
    readonly property string currentItemSource: grid.currentItem ? grid.currentItem.source : ""
    readonly property var currentItemMetadata: grid.currentItem ? grid.currentItem.metadata : undefined
    signal removeImageRequest(var attribute)
    property int defaultCellSize: 160

    implicitWidth: 100
    implicitHeight: 300
    title: "Images"
    property int currentIndex: 0
    readonly property variant viewpoints: cameraInit.attribute('viewpoints').value
    signal filesDropped(var drop)

    ColumnLayout {
        anchors.fill: parent
        spacing: 4

        GridView {
            id: grid

            Layout.fillWidth: true
            Layout.fillHeight: true

            ScrollBar.vertical: ScrollBar {}

            focus: true
            clip: true
            cellWidth: thumbnailSizeSlider.value
            cellHeight: cellWidth
            highlightFollowsCurrentItem: true
            keyNavigationEnabled: true
            model: root.viewpoints

            // Keyboard shortcut to change current image group
            Keys.priority: Keys.BeforeItem
            Keys.onPressed: {
                if(event.modifiers & Qt.AltModifier)
                {
                    event.accepted = true
                    if(event.key == Qt.Key_Right)
                        root.currentIndex = Math.min(root.cameraInits.count - 1, root.currentIndex + 1)
                    else if(event.key == Qt.Key_Left)
                        root.currentIndex = Math.max(0, root.currentIndex - 1)
                }
            }

            delegate: ImageDelegate {
                viewpoint: object.value
                width: grid.cellWidth
                height: grid.cellHeight

                isCurrentItem: grid.currentIndex == index
                onPressed: {
                    grid.currentIndex = index
                    if(mouse.button == Qt.LeftButton)
                        grid.forceActiveFocus()
                }
                onRemoveRequest: removeImageRequest(object)
                Keys.onDeletePressed: removeImageRequest(object)

                // Reconstruction status indicator
                Label {
                    id: statusIndicator
                    property bool inViews: _reconstruction.sfmReport && _reconstruction.isInViews(object)
                    property bool reconstructed: _reconstruction.sfmReport && _reconstruction.isReconstructed(object)

                    font.family: MaterialIcons.fontFamily
                    text: reconstructed ? MaterialIcons.check_circle : MaterialIcons.remove_circle
                    color: reconstructed ? "#4CAF50" : "#F44336"
                    anchors.top: parent.top
                    anchors.right: parent.right
                    anchors.margins: 10
                    font.pointSize: 10
                    visible: inViews
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
                enabled: !root.readOnly
                // TODO: onEntered: call specific method to filter files based on extension
                onDropped: {
                    root.filesDropped(drop)
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

        RowLayout {
            Layout.fillHeight: false
            visible: root.cameraInits.count > 1
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 2

            ToolButton {
                text: MaterialIcons.navigate_before
                font.family: MaterialIcons.fontFamily
                ToolTip.text: "Previous Group (Alt+Left)"
                ToolTip.visible: hovered
                enabled: nodesCB.currentIndex > 0
                onClicked: nodesCB.decrementCurrentIndex()
            }
            Label { text: "Group " }
            ComboBox {
                id: nodesCB
                model: root.cameraInits.count
                implicitWidth: 40
                currentIndex: root.currentIndex
                onActivated: root.currentIndex = currentIndex

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
        anchors.fill: parent

        // Image count
        Label {
            Layout.fillWidth: true
            text: grid.model.count + " image" + (grid.model.count > 1 ? "s" : "")
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
