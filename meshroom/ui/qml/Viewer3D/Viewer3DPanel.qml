import QtQuick
import QtQuick.Controls

import Controls 1.0

/**
 * Viewer3DPanel is the content of the 3D Viewer panel: the Viewer3D and its Inspector3D.
 *
 * It is loaded by URL so that a missing meshViewer plugin (QtAliceVision) only disables this panel.
 */

Panel {
    id: root
    title: "3D Viewer"
    // The title is displayed by the tab of the panel
    headerVisible: false

    property alias viewer3D: c_viewer3D

    MSplitView {
        id: c_viewer3DRowLayout
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
                        c_viewer3D.view(url, undefined)
                    })
                }
            }
        }

        // Inspector Panel
        Inspector3D {
            id: inspector3d
            collection: c_viewer3D.collection
            visible: true
            height: c_viewer3DRowLayout.height
            SplitView.preferredWidth: 260
            SplitView.minimumWidth: 180
            SplitView.maximumWidth: 420
        }
    }
}
