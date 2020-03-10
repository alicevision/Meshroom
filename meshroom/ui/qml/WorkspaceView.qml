import QtQuick 2.7
import QtQuick.Controls 2.3
import QtQuick.Controls 1.4 as Controls1 // For SplitView
import QtQuick.Layouts 1.3
import Qt.labs.platform 1.0 as Platform
import ImageGallery 1.0
import Viewer 1.0
import Viewer3D 1.0
import MaterialIcons 2.2
import Controls 1.0
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
    property bool readOnly: false
    readonly property Viewer3D viewer3D: viewer3D
    readonly property Viewer2D viewer2D: viewer2D

    implicitWidth: 300
    implicitHeight: 400


    // Load a 3D media file in the 3D viewer
    function load3DMedia(filepath) {
        viewer3D.load(filepath);
    }

    Connections {
        target: reconstruction
        onGraphChanged: viewer3D.clear()
        onSfmChanged: viewSfM()
        onSfmReportChanged: viewSfM()
    }
    Component.onCompleted: viewSfM()

    // Load reconstruction's current SfM file
    function viewSfM() {
        if(!reconstruction.sfm)
            return;
        viewer3D.view(reconstruction.sfm.attribute('output'));
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
                cameraInit: reconstruction.cameraInit
                hdrCameraInit: reconstruction.hdrCameraInit
                currentIndex: reconstruction.cameraInitIndex
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
            Layout.minimumWidth: 50

            headerBar: RowLayout {
                MaterialToolButton {
                    text: MaterialIcons.more_vert
                    font.pointSize: 11
                    padding: 2
                    checkable: true
                    checked: imageViewerMenu.visible
                    onClicked: imageViewerMenu.open()
                    Menu {
                        id: imageViewerMenu
                        y: parent.height
                        x: -width + parent.width
                        Action {
                            id: displayImageToolBarAction
                            text: "Display HDR Toolbar"
                            checkable: true
                            checked: true
                            enabled: viewer2D.useFloatImageViewer
                        }
                        Action {
                            id: displayImagePathAction
                            text: "Display Image Path"
                            checkable: true
                            checked: true
                        }
                    }
                }
            }

            Viewer2D {
                id: viewer2D
                anchors.fill: parent

                viewIn3D: root.load3DMedia

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
            implicitWidth: Math.round(parent.width * 0.45)
            Layout.minimumWidth: 20
            Layout.minimumHeight: 80

            Controls1.SplitView {
                anchors.fill: parent
                Viewer3D {
                    id: viewer3D

                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumWidth: 20

                    DropArea {
                        anchors.fill: parent
                        keys: ["text/uri-list"]
                        onDropped: {
                            drop.urls.forEach(function(url){ load3DMedia(url); });
                        }
                    }

                    // Load reconstructed model
                    Button {
                        readonly property var outputAttribute: _reconstruction.texturing ? _reconstruction.texturing.attribute("outputMesh") : null
                        readonly property bool outputReady: outputAttribute && _reconstruction.texturing.globalStatus === "SUCCESS"
                        readonly property int outputMediaIndex: viewer3D.library.find(outputAttribute)

                        text: "Load Model"
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: 10
                        anchors.horizontalCenter: parent.horizontalCenter
                        visible: outputReady && outputMediaIndex == -1
                        onClicked: viewer3D.view(_reconstruction.texturing.attribute("outputMesh"))
                    }
                }

                // Inspector Panel
                Inspector3D {
                    id: inspector3d
                    width: 200
                    Layout.minimumWidth: 5

                    mediaLibrary: viewer3D.library
                    camera: viewer3D.mainCamera
                    uigraph: reconstruction
                    onNodeActivated: _reconstruction.setActiveNodeOfType(node)
                }
            }
        }
    }
}
