pragma Singleton
import QtQuick

import MaterialIcons 2.2

/**
 * Viewer3DSettings singleton gathers properties related to the 3D Viewer capabilities, state and display options.
 */

Item {
    readonly property Component sfmDataLoaderComp: Qt.createComponent("SfmDataLoader.qml")
    readonly property bool supportSfmData: sfmDataLoaderComp.status == Component.Ready
    readonly property Component depthMapLoaderComp: Qt.createComponent("DepthMapLoader.qml")
    readonly property bool supportDepthMap: depthMapLoaderComp.status == Component.Ready

    // Supported 3D files extensions
    readonly property var supportedExtensions: {
        var exts = [".obj", ".stl", ".fbx", ".gltf", ".ply"];
        if (supportSfmData) {
            exts.push(".abc")
            exts.push(".json")
            exts.push(".sfm")
        }
        if (supportDepthMap)
            exts.push(".exr")

        return exts;
    }

    // Available render modes
    readonly property var renderModes: [  // Can't use ListModel because of MaterialIcons expressions
                         {"name": "Solid", "icon": MaterialIcons.crop_din },
                         {"name": "Wireframe", "icon": MaterialIcons.details },
                         {"name": "Textured", "icon": MaterialIcons.texture },
                         {"name": "Spherical Harmonics", "icon": MaterialIcons.brightness_7}
                     ]
    // Current render mode
    property int renderMode: 2

    // Spherical Harmonics file
    property string shlFile: ""
    // Whether to display normals
    property bool displayNormals: false

    // Rasterized point size
    property real pointSize: 1.5
    // Whether point size is fixed or view dependent
    property bool fixedPointSize: false
    property real cameraScale: 0.3
    // Helpers display
    property bool displayGrid: true
    property bool displayGizmo: true
    property bool displayOrigin: false
    property bool displayLightController: false
    // Camera
    property bool syncViewpointCamera: false
    property bool syncWithPickedViewId: false  // Sync active camera with picked view ID from sequence player if the setting is enabled
    property bool viewpointImageOverlay: true
    property real viewpointImageOverlayOpacity: 0.5
    readonly property bool showViewpointImageOverlay: syncViewpointCamera && viewpointImageOverlay
    property bool viewpointImageFrame: false
    readonly property bool showViewpointImageFrame: syncViewpointCamera && viewpointImageFrame

    // Cameras' resection IDs
    property bool displayResectionIds: false
    property int resectionIdCount: 0
    property int resectionId: resectionIdCount
    property var resectionGroups: []  // Number of cameras for each resection ID
}
