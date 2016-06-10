import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import ".."
import "."

ProgressBar {

    id: root
    property variant color: Style.window.color.selected

    style: ProgressBarStyle {
        background: Rectangle {
            color: Style.window.color.xdark
            implicitWidth: 100
            implicitHeight: 18
        }
        progress: Rectangle {
            color: root.color
            Item { // indeterminate mode
                anchors.fill: parent
                anchors.margins: 1
                visible: control.indeterminate
                clip: true
                Row {
                    Repeater {
                        Rectangle {
                            color: index % 2 ? root.color : Qt.darker(root.color, 1.2)
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
    }

}
