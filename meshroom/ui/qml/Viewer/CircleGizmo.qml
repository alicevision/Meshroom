import QtQuick 2.11

Rectangle {
    id: root

    property bool readOnly: false

    signal moved()
    signal incrementRadius(real radiusOffset)

    width: radius * 2
    height: width
    color: "transparent"
    border.width: 5
    border.color: readOnly ? "green" : "yellow"

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

    Behavior on x {
        NumberAnimation {
            duration: 100
        }
    }

    Behavior on y {
        NumberAnimation {
            duration: 100
        }
    }

    Behavior on radius {
        NumberAnimation {
            duration: 100
        }
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
