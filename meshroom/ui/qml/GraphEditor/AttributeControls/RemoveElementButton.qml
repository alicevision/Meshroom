import QtQuick
import QtQuick.Controls

import MaterialIcons 2.2

/**
 * Button that removes an element (e.g. a ListAttribute's child Attribute).
 * Purely presentational: it knows nothing about Attribute/_currentScene; the caller
 * wires `onClicked` to perform the actual removal.
 * Shared by the plain list editor and the table view's frozen first column.
 */
ToolButton {
    id: root

    property bool editable: true

    text: MaterialIcons.remove_circle_outline
    font.family: MaterialIcons.fontFamily
    font.pointSize: 11
    padding: 2
    enabled: root.editable
    ToolTip.text: "Remove Element"
    ToolTip.visible: hovered
    contentItem: Text {
        text: root.text
        font: root.font
        color: palette.text
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }
}
