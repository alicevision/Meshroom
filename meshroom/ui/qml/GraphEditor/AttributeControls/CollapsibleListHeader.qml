import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import MaterialIcons 2.2

/**
 * Collapsible header row shared by the plain ListAttribute editor and the table view:
 * an expand/collapse chevron, an "<n> elements" label and an "Add Element" button.
 * Purely presentational: it knows nothing about Attribute/_currentScene, it just
 * reports user intent through signals for the caller to act on.
 *
 * `expanded` is a one-way inbound binding (parent -> header); the header never assigns
 * to it directly so the parent's binding is never broken. Instead it emits
 * `expandToggled()` and lets the parent flip its own `expanded` state. Likewise,
 * `addRequested()` is emitted instead of the header performing the addition itself.
 *
 * Any extra children declared at instantiation (e.g. TableView's fullscreen button) are
 * appended after the "Add Element" button via the `extraContent` default property.
 */
RowLayout {
    id: root

    spacing: 4
    property bool expanded: false
    required property int elementCount
    property bool editable: true
    default property alias extraContent: trailingRow.data

    signal expandToggled()
    signal addRequested()

    ToolButton {
        text: root.expanded ? MaterialIcons.keyboard_arrow_down : MaterialIcons.keyboard_arrow_right
        font.family: MaterialIcons.fontFamily
        onClicked: root.expandToggled()
    }
    Label {
        Layout.alignment: Qt.AlignVCenter
        text: root.elementCount + " elements"
    }
    AddElementButton {
        editable: root.editable
        onClicked: root.addRequested()
    }
    RowLayout {
        id: trailingRow
        spacing: 4
    }
}
