import QtQuick

/*
Simple selection box that can be used by a MouseArea.

Usage:
1. Create a MouseArea and a SelectionBox.
2. Bind the SelectionBox to the MouseArea by setting the `mouseArea` property.
3. Call startSelection() with coordinates when the selection starts.
4. Call endSelection() when the selection ends.
5. Listen to the selectionEnded signal to get the selection rectangle.
*/

Item {
    id: root

    property MouseArea mouseArea
    property alias color: selectionBox.color
    property alias border: selectionBox.border

    readonly property bool active: mouseArea.drag.target == dragTarget

    signal selectionEnded(rect selectionRect, int modifiers)

    function startSelection(mouse) {
        dragTarget.startPos.x = dragTarget.x = mouse.x;
        dragTarget.startPos.y = dragTarget.y = mouse.y;
        dragTarget.modifiers = mouse.modifiers;
        mouseArea.drag.target = dragTarget;
    }

    function endSelection() {
        if (!active) {
            return;
        }
        mouseArea.drag.target = null;
        const rect = Qt.rect(selectionBox.x, selectionBox.y, selectionBox.width, selectionBox.height)
        selectionEnded(rect, dragTarget.modifiers);
    }

    visible: active

    Rectangle {
        id: selectionBox
        color: "#109b9b9b"
        border.width: 1
        border.color: "#b4b4b4"

        x: Math.min(dragTarget.startPos.x, dragTarget.x)
        y: Math.min(dragTarget.startPos.y, dragTarget.y)
        width: Math.abs(dragTarget.x - dragTarget.startPos.x)
        height: Math.abs(dragTarget.y - dragTarget.startPos.y)
    }

    Item {
        id: dragTarget
        property point startPos
        property var modifiers
    }
}
