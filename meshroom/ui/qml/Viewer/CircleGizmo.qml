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

    Rectangle {
        color: parent.color
        anchors.centerIn: parent
        width: 20
        height: 2
    }
    Rectangle {
        color: parent.color
        anchors.centerIn: parent
        width: 2
        height: 20
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

    MouseArea {
        id: mArea
        enabled: !root.readOnly
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
        drag.target: parent

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
