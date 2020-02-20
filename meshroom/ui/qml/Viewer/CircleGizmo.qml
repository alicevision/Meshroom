import QtQuick 2.11

Rectangle {
    id: root

    signal moved()

    width: radius * 2
    height: width
    color: "transparent"
    border.width: 5
    border.color: "yellow"

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
        anchors.fill: parent
        cursorShape: Qt.OpenHandCursor
        acceptedButtons: Qt.LeftButton
        hoverEnabled: true
        drag.target: parent

        drag.onActiveChanged:
        {
            if(!drag.active)
            {
                cursorShape = Qt.OpenHandCursor;
                moved();
            }
            else
            {
                cursorShape = Qt.ClosedHandCursor;
            }
        }
    }
}
