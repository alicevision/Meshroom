import QtQuick 2.7
import QtQuick.Controls 2.3
import QtQuick.Controls 1.4 as Controls1 // For SplitView
import QtQuick.Layouts 1.3
import Qt.labs.platform 1.0 as Platform
import Viewer 1.0
import MaterialIcons 2.2
import "filepath.js" as Filepath


/**
 * WorkspaceView is an aggregation of Meshroom's main modules.
 *
 * It contains an ImageGallery, a 2D and a 3D viewer to manipulate and visualize reconstruction data.
 */
Item {
    id: root

    property variant reconstruction: _reconstruction
    readonly property variant cameraInits: _reconstruction.cameraInits
    readonly property string meshFile: _reconstruction.meshFile
    property bool readOnly: false

    implicitWidth: 300
    implicitHeight: 400

    onMeshFileChanged: viewer3D.clear()

    signal requestGraphAutoLayout()

    // Load a 3D media file in the 3D viewer
    function load3DMedia(filepath)
    {
        if(Filepath.extension(filepath) === ".abc")
            viewer3D.abcSource = filepath
        else
            viewer3D.source = filepath
    }

    SystemPalette { id: palette }

    Controls1.SplitView {
        anchors.fill: parent

        Controls1.SplitView {
            orientation: Qt.Vertical
            Layout.fillHeight: true
            Layout.minimumWidth: imageGallery.defaultCellSize

            ImageGallery {
                id: imageGallery
                Layout.fillHeight: true
                cameraInits: root.cameraInits
                cameraInit: _reconstruction.cameraInit
                currentIndex: reconstruction.cameraInitIndex
                onCurrentIndexChanged: reconstruction.cameraInitIndex = currentIndex
                onRemoveImageRequest: reconstruction.removeAttribute(attribute)
                onFilesDropped: reconstruction.handleFilesDrop(drop, cameraInit)
            }
            LiveSfmView {
                visible: settings_UILayout.showLiveReconstruction
                reconstruction: root.reconstruction
                Layout.fillWidth: true
                Layout.preferredHeight: childrenRect.height
                onRequestGraphAutoLayout: graphEditor.doAutoLayout()
            }
        }
        Panel {
            title: "Image Viewer"
            Layout.fillHeight: true
            implicitWidth: Math.round(parent.width * 0.4)
            Layout.minimumWidth: 40
            Viewer2D {
                id: viewer2D
                anchors.fill: parent
                property url imageGallerySource: imageGallery.currentItemSource
                onImageGallerySourceChanged: viewer2D.source = imageGallerySource
                DropArea {
                    anchors.fill: parent
                    onDropped: viewer2D.source = drop.urls[0]
                }
                Rectangle {
                    z: -1
                    anchors.fill: parent
                    color: Qt.darker(palette.base, 1.1)
                }
            }
        }

        Panel {
            title: "3D Viewer"
            implicitWidth: Math.round(parent.width * 0.33)
            Layout.minimumWidth: 20
            Layout.minimumHeight: 80

            Viewer3D {
                id: viewer3D
                anchors.fill: parent
                DropArea {
                    anchors.fill: parent
                    onDropped: load3DMedia(drop.urls[0])
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
