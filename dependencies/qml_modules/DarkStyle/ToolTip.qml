import QtQuick 2.7
import QtQuick.Templates 2.0 as T

import "."

T.ToolTip {

    id: control
    x: parent ? (parent.width - implicitWidth) / 2 : 0
    y: -implicitHeight - 5
    implicitWidth: Math.max(background ? background.implicitWidth : 0,
                            contentItem.implicitWidth + leftPadding + rightPadding)
    implicitHeight: Math.max(background ? background.implicitHeight : 0,
                             contentItem.implicitHeight + topPadding + bottomPadding)
    closePolicy: T.Popup.CloseOnEscape | T.Popup.CloseOnPressOutsideParent | T.Popup.CloseOnReleaseOutsideParent
    margins: 8
    padding: 8

    enter: Transition {
        NumberAnimation { property: "opacity"; from: 0.0; to: 1.0; easing.type: Easing.OutQuad; duration: 500 }
    }
    exit: Transition {
        NumberAnimation { property: "opacity"; from: 1.0; to: 0.0; easing.type: Easing.InQuad; duration: 500 }
    }
    contentItem: Text {
        text: control.text
        font: control.font
        color: "black"
    }
    background: Rectangle {
        implicitHeight: 32
        color: Globals.window.color.xlight
        opacity: 0.9
    }
}
