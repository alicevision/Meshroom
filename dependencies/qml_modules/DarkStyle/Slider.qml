import QtQuick 2.7
import QtQuick.Templates 2.0 as T

import "."

T.Slider {

    id: control
    implicitWidth: 200
    implicitHeight: 30

    handle: Rectangle {
        x: control.leftPadding + (control.visualPosition * (control.availableWidth - width))
        y: control.topPadding + (control.availableHeight - height) / 2
        width: 2
        height: control.availableHeight / 2
        color: Globals.window.color.selected
    }
    background: Item {
        Rectangle {
            width: parent.width
            height: 2
            y: (parent.height - height) / 2
            color: Globals.window.color.dark
            Rectangle {
                x: 0
                y: (parent.height - height) / 2
                width: control.position * parent.width
                height: parent.height
                color: Globals.window.color.selected
            }
        }
    }

}
