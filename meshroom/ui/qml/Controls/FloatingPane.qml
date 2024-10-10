import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

/**
 * FloatingPane provides a Pane with a slightly transparent default background
 * using palette.base as color. Useful to create floating toolbar/overlays.
 */

Pane {
    id: root

    property bool opaque: false
    property int radius: 1

    padding: 6
    anchors.margins: 2
    background: Rectangle {
        color: root.palette.base
        opacity: opaque ? 1.0 : 0.7
        radius: root.radius
    }
}
