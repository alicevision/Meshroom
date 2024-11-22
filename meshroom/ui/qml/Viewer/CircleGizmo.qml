import QtQuick

Item {
    id: root

    property bool readOnly: false

    signal moved(real xoffset, real yoffset)
    signal incrementRadius(real radiusOffset)

    // Circle
    property real circleX: 0.
    property real circleY: 0.
    Rectangle {
        id: circle

        width: radius * 2
        height: width

        x: circleX + (root.width - width) / 2
        y: circleY + (root.height - height) / 2

        color: "transparent"
        border.width: 5
        border.color: readOnly ? "green" : "yellow"

        // Cross to visualize the circle center
        Rectangle {
            color: parent.border.color
            anchors.centerIn: parent
            width: parent.width * 0.2
            height: parent.border.width * 0.5
        }
        Rectangle {
            color: parent.border.color
            anchors.centerIn: parent
            width: parent.border.width * 0.5
            height: parent.height * 0.2
        }

        Loader {
            anchors.fill: parent
            active: !root.readOnly

            sourceComponent: MouseArea {
                id: mArea
                anchors.fill: parent
                cursorShape: root.readOnly ? Qt.ArrowCursor : (controlModifierEnabled ? Qt.SizeBDiagCursor : (pressed ? Qt.ClosedHandCursor : Qt.OpenHandCursor))
                propagateComposedEvents: true

                property bool controlModifierEnabled: false
                onPositionChanged: function(mouse) {
                    mArea.controlModifierEnabled = (mouse.modifiers & Qt.ControlModifier)
                    mouse.accepted = false
                }
                acceptedButtons: Qt.LeftButton
                hoverEnabled: true
                drag.target: circle

                drag.onActiveChanged: {
                    if (!drag.active) {
                        root.moved(circle.x - (root.width - circle.width) / 2, circle.y - (root.height - circle.height) / 2)
                    }
                }
                onPressed: {
                    forceActiveFocus()
                }
                onWheel: function(wheel) {
                    mArea.controlModifierEnabled = (wheel.modifiers & Qt.ControlModifier)
                    if (wheel.modifiers & Qt.ControlModifier) {
                        root.incrementRadius(wheel.angleDelta.y / 120.0)
                        wheel.accepted = true
                    } else {
                        wheel.accepted = false
                    }
                }
            }
        }
    }
    property alias circleRadius: circle.radius
    property alias circleBorder: circle.border

    /*
    // visualize top-left corner for debugging purpose
    Rectangle {
        color: "red"
        width: 500
        height: 50
    }
    Rectangle {
        color: "red"
        width: 50
        height: 500
    }
    */
}
