import QtQuick 2.7
import QtQuick.Templates 2.0 as T

import "."

T.MenuItem {
    id: control

    implicitWidth: Math.max(background ? background.implicitWidth : 0,
                            contentItem.implicitWidth + leftPadding + rightPadding)
    implicitHeight: Math.max(background ? background.implicitHeight : 0,
                             Math.max(contentItem.implicitHeight,
                                      indicator ? indicator.implicitHeight : 0) + topPadding + bottomPadding)
    // baselineOffset: contentItem.y + contentItem.baselineOffset

    padding: 10
    hoverEnabled: true

    // indicator: Item {
    //     x: text ? (control.mirrored ? control.width - width - control.rightPadding : control.leftPadding) : control.leftPadding + (control.availableWidth - width) / 2
    //     y: control.topPadding + (control.availableHeight - height) / 2
    //     visible: control.checkable
    // }
    contentItem: Label {
        text: control.text
        state: "small"
    }
    background: Rectangle {
        implicitWidth: 200
        implicitHeight: 30
        color: (control.highlighted || control.hovered) ? Qt.rgba(1, 1, 1, 0.1) : Qt.rgba(0, 0, 0, 0.1)
        Behavior on color { ColorAnimation {} }
    }
}
