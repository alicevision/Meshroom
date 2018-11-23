pragma Singleton
import QtQuick 2.9

/**
 * Viewer3DSettings singleton gathers properties related to the 3D Viewer capabilities, state and display options.
 */
Item {
    readonly property Component abcLoaderComp: Qt.createComponent("AlembicLoader.qml")
    readonly property bool supportAlembic: abcLoaderComp.status == Component.Ready
    readonly property Component depthMapLoaderComp: Qt.createComponent("DepthMapLoader.qml")
    readonly property bool supportDepthMap: depthMapLoaderComp.status == Component.Ready

    // Rasterized point size
    property real pointSize: 4

}
