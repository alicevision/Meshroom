import QtQuick

/**
 * MouseArea tracking which button is dragging and where the drag started.
 * Gives keyboard focus to @p focusTarget on press, so that its Keys handlers receive key events.
 */
MouseArea {
    id: root

    property Item focusTarget: null

    property real initialX: 0
    property real initialY: 0
    property bool draggingLeft: false
    property bool draggingMiddle: false
    property bool draggingRight: false
    readonly property bool dragging: draggingLeft || draggingMiddle || draggingRight

    acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton

    onPressed: (mouse) => {
        if (focusTarget)
        {
            focusTarget.forceActiveFocus()
        }

        initialX = mouse.x
        initialY = mouse.y
        draggingLeft = (mouse.button === Qt.LeftButton)
        draggingMiddle = (mouse.button === Qt.MiddleButton)
        draggingRight = (mouse.button === Qt.RightButton)
    }

    onReleased: (mouse) => {
        if (mouse.button === Qt.LeftButton)
        {
            draggingLeft = false
        }
        else if (mouse.button === Qt.MiddleButton)
        {
            draggingMiddle = false
        }
        else if (mouse.button === Qt.RightButton)
        {
            draggingRight = false
        }
    }
}
