import QtQuick
import QtQuick.Controls

import MaterialIcons 2.2

/**
 * Button that appends a new element to a ListAttribute.
 * Shared by the plain list editor, the table view header and its fullscreen corner cell.
 */
ToolButton {
    id: root

    property bool editable: true

    text: MaterialIcons.add_circle_outline
    font.family: MaterialIcons.fontFamily
    font.pointSize: 11
    padding: 2
    enabled: root.editable
    ToolTip.text: "Add Element"
    ToolTip.visible: hovered
    contentItem: Text {
        text: root.text
        font: root.font
        color: palette.text
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }
}
