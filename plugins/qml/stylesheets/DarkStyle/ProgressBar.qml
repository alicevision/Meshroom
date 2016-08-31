import QtQuick 2.7
import QtQuick.Templates 2.0 as T

import "."

T.ProgressBar {

    id: control
    implicitWidth: 200
    implicitHeight: 30
    contentItem: Item {
        Item {
            width: control.availableWidth * control.position
            height: control.availableHeight
            clip: true
            Row {
                Repeater {
                    Rectangle {
                        color: index % 2 ? Globals.window.color.selected : Qt.darker(Globals.window.color.selected, 1.2)
                        width: 20
                        height: control.height
                    }
                    model: control.width / 20 + 2
                }
                XAnimator on x {
                    from: 0 ; to: -40
                    loops: Animation.Infinite
                    running: control.indeterminate
                }
            }
        }
    }
    background: Rectangle {
        x: control.leftPadding
        y: control.topPadding + (control.availableHeight - height) / 2
        color: Globals.window.color.dark
    }

}
