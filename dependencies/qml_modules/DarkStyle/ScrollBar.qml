import QtQuick 2.7
import QtQuick.Templates 2.0 as T

import "."

T.ScrollBar {

    id: control
    implicitWidth: Math.max(background ? background.implicitWidth : 0,
                            contentItem.implicitWidth + leftPadding + rightPadding)
    implicitHeight: Math.max(background ? background.implicitHeight : 0,
                             contentItem.implicitHeight + topPadding + bottomPadding)

    contentItem: Rectangle {
        id: handle
        implicitWidth: 4
        implicitHeight: 4
        color: control.pressed ? Globals.window.color.selected : Globals.window.color.xlight
        visible: control.size < 1.0
        opacity: 0.0
        states: State {
            name: "active"
            when: control.active
            PropertyChanges { target: handle; opacity: 0.75 }
        }
        transitions: Transition {
            from: "active"
            SequentialAnimation {
                PauseAnimation { duration: 800 }
                NumberAnimation { target: handle; duration: 400; property: "opacity"; to: 0.0 }
            }
        }
    }
}
