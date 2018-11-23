import QtQuick 2.7
import QtQuick.Controls 2.3
import QtQuick.Controls 1.4 as Controls1 // For SplitView
import QtQuick.Layouts 1.3
import Qt.labs.platform 1.0 as Platform
import Viewer 1.0
import Viewer3D 1.0
import MaterialIcons 2.2
import Utils 1.0


/**
 * WorkspaceView is an aggregation of Meshroom's main modules.
 *
 * It contains an ImageGallery, a 2D and a 3D viewer to manipulate and visualize reconstruction data.
 */
Item {
    id: root

    property variant reconstruction: _reconstruction
    readonly property variant cameraInits: _reconstruction.cameraInits
    readonly property url meshFile: Filepath.stringToUrl(_reconstruction.meshFile)
    property bool readOnly: false

    implicitWidth: 300
    implicitHeight: 400


    // Load a 3D media file in the 3D viewer
    function load3DMedia(filepath)
    {
        if(!Filepath.exists(Filepath.urlToString(filepath)))
            return
        switch(Filepath.extension(filepath))
        {
        case ".abc": viewer3D.abcSource = filepath; break;
        case ".exr": viewer3D.depthMapSource = filepath; break;
        case ".obj": viewer3D.source = filepath; break;
        }
    }

    Connections {
        target: reconstruction
        onGraphChanged: {
            viewer3D.clear()
            viewer2D.clear()
        }
        onSfmReportChanged: {
            viewer3D.abcSource = ''
            if(!reconstruction.sfm)
                return
            load3DMedia(Filepath.stringToUrl(reconstruction.sfm.attribute('output').value))
        }
    }

    SystemPalette { id: activePalette }

    Controls1.SplitView {
        anchors.fill: parent

        Controls1.SplitView {
            orientation: Qt.Vertical
            Layout.fillHeight: true
            Layout.minimumWidth: imageGallery.defaultCellSize

            ImageGallery {
                id: imageGallery
                Layout.fillHeight: true
                readOnly: root.readOnly
                cameraInits: root.cameraInits
                cameraInit: _reconstruction.cameraInit
                currentIndex: reconstruction.cameraInitIndex
                onCurrentIndexChanged: reconstruction.cameraInitIndex = currentIndex
                onRemoveImageRequest: reconstruction.removeAttribute(attribute)
                onFilesDropped: reconstruction.handleFilesDrop(drop, augmentSfm ? null : cameraInit)
            }
            LiveSfmView {
                visible: settings_UILayout.showLiveReconstruction
                reconstruction: root.reconstruction
                Layout.fillWidth: true
                Layout.preferredHeight: childrenRect.height
            }
        }
        Panel {
            title: "Image Viewer"
            Layout.fillHeight: true
            Layout.fillWidth: true
            Layout.minimumWidth: 40
            Viewer2D {
                id: viewer2D
                anchors.fill: parent

                Connections {
                    target: imageGallery
                    onCurrentItemChanged: {
                        viewer2D.source = imageGallery.currentItemSource
                        viewer2D.metadata = imageGallery.currentItemMetadata
                    }
                }

                DropArea {
                    anchors.fill: parent
                    keys: ["text/uri-list"]
                    onDropped: {
                        viewer2D.source = drop.urls[0]
                        viewer2D.metadata = {}
                    }
                }
                Rectangle {
                    z: -1
                    anchors.fill: parent
                    color: Qt.darker(activePalette.base, 1.1)
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
                    keys: ["text/uri-list"]
                    onDropped: load3DMedia(drop.urls[0])
                }
            }

            Label {
                anchors.centerIn: parent
                text: "Loading..."
                visible: viewer3D.loading
                padding: 6
                background: Rectangle { color: parent.palette.base; opacity: 0.5 }
            }

            // Load reconstructed model
            Button {
                text: "Load Model"
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 10
                anchors.horizontalCenter: parent.horizontalCenter
                visible: meshFile != "" && (viewer3D.source != meshFile)
                onClicked: load3DMedia(meshFile)
            }
        }
    }
}
