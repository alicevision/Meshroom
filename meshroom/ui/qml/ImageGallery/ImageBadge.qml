import QtQuick

import MaterialIcons 2.2
import Utils 1.0

/**
 * ImageBadge is a preset MaterialLabel to display an icon bagdge on an image.
 */

MaterialLabel {
    id: root

    font.pointSize: 10
    padding: 2
    background: Rectangle {
        color: Colors.sysPalette.window
        opacity: 0.6
    }
}
