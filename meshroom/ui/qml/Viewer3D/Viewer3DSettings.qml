pragma Singleton
import QtQuick 2.9
import MaterialIcons 2.2

/**
 * Viewer3DSettings singleton gathers properties related to the 3D Viewer capabilities, state and display options.
 */
Item {
    readonly property Component abcLoaderComp: Qt.createComponent("AlembicLoader.qml")
    readonly property bool supportAlembic: abcLoaderComp.status == Component.Ready
    readonly property Component depthMapLoaderComp: Qt.createComponent("DepthMapLoader.qml")
    readonly property bool supportDepthMap: depthMapLoaderComp.status == Component.Ready

    // Available render modes
    readonly property var renderModes: [ // Can't use ListModel because of MaterialIcons expressions
                         {"name": "Solid", "icon": MaterialIcons.crop_din },
                         {"name": "Wireframe", "icon": MaterialIcons.grid_on },
                         {"name": "Textured", "icon": MaterialIcons.texture },
                     ]
    // Current render mode
    property int renderMode: 2

    // Rasterized point size
    property real pointSize: 1.5
    // Whether point size is fixed or view dependent
    property bool fixedPointSize: false
    property real cameraScale: 0.3
    // Helpers display
    property bool displayGrid: true
    property bool displayGizmo: true
    property bool displayLocator: false
}
