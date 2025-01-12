import QtQuick
import QtQuick.Shapes

/*
Simple selection line that can be used by a MouseArea.

Usage:
1. Create a MouseArea and a selectionShape.
2. Bind the selectionShape to the MouseArea by setting the `mouseArea` property.
3. Call startSelection() with coordinates when the selection starts.
4. Call endSelection() when the selection ends.
5. Listen to the selectionEnded signal to get the rectangle whose Diagonal is the selection line.
*/

Item {
    id: root

    property MouseArea mouseArea

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
        const rect = Qt.rect(selectionShape.x, selectionShape.y, selectionShape.width, selectionShape.height)
        selectionEnded(rect, dragTarget.modifiers);
    }

    visible: active

    Item {
        id: selectionShape
        x: dragTarget.startPos.x
        y: dragTarget.startPos.y
        width: dragTarget.x - dragTarget.startPos.x
        height: dragTarget.y - dragTarget.startPos.y

        Shape {
            id: dynamicLine;
            width: selectionShape.width;
            height: selectionShape.height;
            anchors.fill: parent;

            ShapePath {
                strokeWidth: 2;
                strokeStyle: ShapePath.DashLine;
                strokeColor: "#FF0000";
                dashPattern: [3, 2];

                startX: 0;
                startY: 0;

                PathLine {
                    x: selectionShape.width;
                    y: selectionShape.height;
                }
            }
        }
    }

    Item {
        id: dragTarget
        property point startPos
        property var modifiers
    }
}
