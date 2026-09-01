import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Utils 1.0

/**
 * FloatingPane provides a Pane with a slightly transparent default background
 * using palette.base as color. Useful to create floating toolbar/overlays.
 */

Pane {
    id: root

    property bool opaque: false
    property int radius: UISettings.dp(1)

    padding: UISettings.dp(6)
    anchors.margins: UISettings.dp(2)
    background: Rectangle {
        color: root.palette.base
        opacity: opaque ? 1.0 : 0.7
        radius: root.radius
    }
}
