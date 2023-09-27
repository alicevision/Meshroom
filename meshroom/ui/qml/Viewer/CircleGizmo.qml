import QtQuick 2.15

Item {
    id: root

    property bool readOnly: false

    signal moved()
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

    Loader {
        anchors.fill: parent
        active: !root.readOnly

        sourceComponent: MouseArea {
            id: mArea
            anchors.fill: parent
            cursorShape: root.readOnly ? Qt.ArrowCursor : (controlModifierEnabled ? Qt.SizeBDiagCursor : (pressed ? Qt.ClosedHandCursor : Qt.OpenHandCursor))
            propagateComposedEvents: true

            property bool controlModifierEnabled: false
            onPositionChanged: {
                mArea.controlModifierEnabled = (mouse.modifiers & Qt.ControlModifier)
                mouse.accepted = false;
            }
            acceptedButtons: Qt.LeftButton
            hoverEnabled: true
            drag.target: root

            drag.onActiveChanged: {
                if(!drag.active) {
                    moved();
                }
            }
            onPressed: {
                forceActiveFocus();
            }
            onWheel: {
                mArea.controlModifierEnabled = (wheel.modifiers & Qt.ControlModifier)
                if (wheel.modifiers & Qt.ControlModifier) {
                    incrementRadius(wheel.angleDelta.y / 120.0);
                    wheel.accepted = true;
                } else {
                    wheel.accepted = false;
                }
            }
        }
    }
}
