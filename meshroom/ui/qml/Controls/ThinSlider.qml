import QtQuick
import QtQuick.Controls

/**
 * A thin, professional-looking Slider with a narrow track and a small circular handle.
 * Drop-in replacement for the standard QtQuick.Controls Slider.
 */
Slider {
    id: control

    implicitHeight: 20

    background: Rectangle {
        x: control.leftPadding
        y: control.topPadding + control.availableHeight / 2 - height / 2
        width: control.availableWidth
        height: 3
        radius: 1.5
        color: control.palette.mid

        Rectangle {
            width: control.visualPosition * parent.width
            height: parent.height
            radius: parent.radius
            color: control.palette.highlight
        }
    }

    handle: Rectangle {
        x: control.leftPadding + control.visualPosition * (control.availableWidth - width)
        y: control.topPadding + control.availableHeight / 2 - height / 2
        width: 12
        height: 12
        radius: 6
        color: control.pressed ? control.palette.highlight : control.palette.button
        border.color: control.hovered || control.pressed ? control.palette.highlight : control.palette.mid
        border.width: 1
    }
}
