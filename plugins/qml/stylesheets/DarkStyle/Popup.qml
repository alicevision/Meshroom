import QtQuick 2.7
import QtQuick.Templates 2.0 as T

import "."

T.Popup {

    id: control

    implicitWidth: parent ? parent.width * 0.5 : 200
    implicitHeight: parent ? parent.height * 0.5 : 200
    x: parent ? (parent.width - width) * 0.5 : 0
    y: parent ? (parent.height - height) * 0.5 : 0
    modal: true
    focus: true

    enter: Transition {
        NumberAnimation { property: "scale"; from: 0.9; to: 1.0; easing.type: Easing.OutQuint; duration: 220 }
        NumberAnimation { property: "opacity"; from: 0.0; to: 1.0; easing.type: Easing.OutCubic; duration: 150 }
    }
    exit: Transition {
        NumberAnimation { property: "scale"; from: 1.0; to: 0.9; easing.type: Easing.OutQuint; duration: 220 }
        NumberAnimation { property: "opacity"; from: 1.0; to: 0.0; easing.type: Easing.OutCubic; duration: 150 }
    }
    contentItem: Item {}
    background: Rectangle {
        color: Globals.window.color.dark
    }

}
