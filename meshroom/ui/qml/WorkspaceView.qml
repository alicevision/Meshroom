import QtQuick 2.15
import QtQuick.Controls 2.15
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
        function onGraphChanged() { viewer3D.clear() }
        function onSfmChanged() { viewSfM() }
        function onSfmReportChanged() { viewSfM() }
    }
    Component.onCompleted: viewSfM()

    // Load reconstruction's current SfM file
    function viewSfM() {
        var activeNode = _reconstruction.activeNodes.get('sfm').node;
        if(!activeNode)
            return;
        viewer3D.view(activeNode.attribute('output'));
    }

    SystemPalette { id: activePalette }

    SplitView {
        anchors.fill: parent

        SplitView {
            orientation: Qt.Vertical
            SplitView.fillHeight: true
            SplitView.preferredWidth : Math.round(parent.width * 0.17)
            SplitView.minimumWidth: imageGallery.defaultCellSize

            ImageGallery {
                id: imageGallery
                SplitView.fillHeight: true
                readOnly: root.readOnly
                cameraInits: root.cameraInits
                cameraInit: reconstruction.cameraInit
                tempCameraInit: reconstruction.tempCameraInit
                currentIndex: reconstruction.cameraInitIndex
                onRemoveImageRequest: reconstruction.removeAttribute(attribute)
                onFilesDropped: reconstruction.handleFilesDrop(drop, augmentSfm ? null : cameraInit)
            }
            LiveSfmView {
                visible: settings_UILayout.showLiveReconstruction
                reconstruction: root.reconstruction
                SplitView.fillWidth: true
                SplitView.preferredHeight: childrenRect.height
            }
        }
        Panel {
            title: "Image Viewer"
            SplitView.fillWidth: true
            SplitView.minimumWidth: 50
            loading: viewer2D.loadingModules.length > 0
            loadingText: loading ? "Loading " + viewer2D.loadingModules : ""

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
                    function onCurrentItemChanged() {
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
            SplitView.minimumWidth: 20
            SplitView.minimumHeight: 80

            SplitView {
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
                    onNodeActivated: _reconstruction.setActiveNode(node)
                }
            }
        }
    }
}
