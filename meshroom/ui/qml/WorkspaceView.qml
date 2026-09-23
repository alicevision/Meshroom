import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Controls 1.0
import Docking 1.0
import MaterialIcons 2.2
import ImageGallery 1.0
import Viewer 1.0
import Viewer3D 1.0

/**
 * WorkspaceView is an aggregation of Meshroom's main modules.
 *
 * It contains an ImageGallery, a 2D, a text and a 3D viewer to manipulate and visualize scene data.
 * They are declared as DockPanels (see `dockPanels`): a DockManager displays them where the layout of
 * the panels says, this item is not displayed itself.
 */

Item {
    id: root

    property variant currentScene: _currentScene
    readonly property variant cameraInits: _currentScene ? _currentScene.cameraInits : null
    property bool readOnly: false
    property alias panel3dViewer: panel3dViewerLoader.item
    readonly property Viewer2D viewer2D: viewer2D
    readonly property alias imageGallery: imageGallery
    readonly property TextViewer viewerText: textViewer
    /// The panels to dock
    readonly property var dockPanels: [imageGalleryPanel, imageViewerPanel, textViewerPanel, viewer3DPanel]

    visible: false

    // Load a 3D media file in the 3D viewer
    function load3DMedia(filepath, label = undefined) {
        if (panel3dViewerLoader.active) {
            panel3dViewerLoader.item.viewer3D.load(filepath, label)
        }
    }

    Connections {
        target: currentScene
        function onGraphChanged() {
            if (panel3dViewerLoader.active) {
                panel3dViewerLoader.item.viewer3D.clear()
            }
        }
        function onSfmChanged() { viewSfM() }
        function onSfmReportChanged() { viewSfM() }
    }
    Component.onCompleted: viewSfM()

    // Load the current scene's SfM file
    function viewSfM() {
        var activeNode = _currentScene.activeNodes ? _currentScene.activeNodes.get('sfm').node : null
        if (!activeNode)
            return
        if (panel3dViewerLoader.active) {
            panel3dViewerLoader.item.viewer3D.view(activeNode.attribute('output'))
        }
    }

    SystemPalette { id: activePalette }

    DockPanel {
        id: imageGalleryPanel
        panelId: "imageGallery"
        title: "Image Gallery"
        toolBar: imageGallery.headerBarItem

        ImageGallery {
            id: imageGallery
            anchors.fill: parent
            headerVisible: false
            readOnly: root.readOnly
            cameraInits: root.cameraInits
            cameraInit: currentScene ? currentScene.cameraInit : null
            tempCameraInit: currentScene ? currentScene.tempCameraInit : null
            cameraInitIndex: currentScene ? currentScene.cameraInitIndex : -1
            onRemoveSelectedImagesRequest: function(objects) { currentScene.removeImages(objects) }
            onAllViewpointsCleared: currentScene.selectedViewId = "-1"
            onFilesDropped: function(drop) {
                if (drop["meshroomScenes"].length == 1 || drop["meshroomTemplates"].length == 1) {
                    ensureSaved(function() {
                        if (currentScene.handleFilesUrl(drop, cameraInit)) {
                            if (currentScene.graph.filepath)
                                MeshroomApp.addRecentProjectFile(drop["meshroomScenes"][0])
                            else if (drop["meshroomTemplates"].length == 1)
                                MeshroomApp.addRecentTemplateFile(drop["meshroomTemplates"][0])
                            else
                                MeshroomApp.addRecentTemplateFile(drop["meshroomScenes"][0])
                        }
                    })
                } else {
                    currentScene.handleFilesUrl(drop, cameraInit)
                }
            }
        }
    }

    DockPanel {
        id: imageViewerPanel
        panelId: "imageViewer"
        title: "Image Viewer"

        toolBar: RowLayout {
            spacing: 4

            // Loading indicator for image viewer
            BusyIndicator {
                id: mediaViewerLoadingIndicator
                padding: 0
                implicitWidth: 12
                implicitHeight: 12
                running: viewer2D.loadingModules.length > 0
                visible: running
            }
            Label {
                visible: mediaViewerLoadingIndicator.visible
                text: "Loading " + viewer2D.loadingModules
                font.italic: true
            }

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
                        id: displayLensDistortionToolBarAction
                        text: "Display Lens Distortion Toolbar"
                        checkable: true
                        checked: true
                        enabled: viewer2D.useLensDistortionViewer
                    }
                    Action {
                        id: displayPanoramaToolBarAction
                        text: "Display Panorama Toolbar"
                        checkable: true
                        checked: true
                        enabled: viewer2D.usePanoramaViewer
                    }
                    Action {
                        id: displayImagePathAction
                        text: "Display Image Path"
                        checkable: true
                        checked: true && !viewer2D.usePanoramaViewer
                    }
                    Action {
                        id: enable8bitViewerAction
                        text: "Enable 8-bit Viewer"
                        checkable: true
                        checked: MeshroomApp.default8bitViewerEnabled
                    }
                    Action {
                        id: enableSequencePlayerAction
                        text: "Enable Sequence Player"
                        checkable: true
                        checked: MeshroomApp.defaultSequencePlayerEnabled
                    }
                }
            }
        }

        Viewer2D {
            id: viewer2D
            anchors.fill: parent

            viewIn3D: root.load3DMedia

            DropArea {
                anchors.fill: parent
                keys: ["text/uri-list"]
                onDropped: function(drop) {
                    viewer2D.loadExternal(drop.urls[0]);
                }
            }
            Rectangle {
                z: -1
                anchors.fill: parent
                color: Qt.darker(activePalette.base, 1.1)
            }
        }
    }

    DockPanel {
        id: textViewerPanel
        panelId: "textViewer"
        title: "Text Viewer"

        TextViewer {
            id: textViewer
            anchors.fill: parent

            DropArea {
                anchors.fill: parent
                keys: ["text/uri-list"]
                onDropped: function(drop) {
                    textViewer.source = drop.urls[0]
                }
            }
        }
    }

    DockPanel {
        id: viewer3DPanel
        panelId: "viewer3D"
        title: "3D Viewer"

        Loader {
            id: panel3dViewerLoader
            // Closing the panel unloads the 3D scene
            active: _dockLayout.openPanels.indexOf("viewer3D") !== -1
            visible: active
            anchors.fill: parent
            sourceComponent: panel3dViewerComponent
        }
    }

    Component {
        id: panel3dViewerComponent
        Panel {
            id: panel3dViewer
            title: "3D Viewer"
            // The title is displayed by the tab of the panel
            headerVisible: false

            property alias viewer3D: c_viewer3D

            MSplitView {
                id: c_viewer3DSplitView
                anchors.fill: parent
                orientation: Qt.Horizontal
                Viewer3D {
                    id: c_viewer3D

                    SplitView.fillWidth: true
                    SplitView.minimumWidth: 50

                    DropArea {
                        anchors.fill: parent
                        keys: ["text/uri-list"]
                        onDropped: function(drop) {
                            drop.urls.forEach(function(url) {
                                load3DMedia(url)
                            })
                        }
                    }

                    Connections {
                        target: viewer2D
                        function onSync3DSelectedChanged() {
                            Viewer3DSettings.syncWithPickedViewId = viewer2D.sync3DSelected
                        }
                    }
                }
                
                // Inspector Panel
                Inspector3D {
                    id: inspector3d
                    SplitView.preferredWidth: 220
                    SplitView.minimumWidth: 100

                    mediaLibrary: c_viewer3D.library
                    camera: c_viewer3D.mainCamera
                    uigraph: currentScene
                    onNodeActivated: _currentScene.setActiveNode(node)
                }
            }
        }
    }
}
