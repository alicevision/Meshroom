import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import ".."
import "."

Slider {

    id: root

    style: SliderStyle {
        handle: Rectangle {
            width: 15
            height: 15
            radius: height
            antialiasing: true
            color: control.enabled ? Style.window.color.selected : Style.window.color.xlight
        }
        groove: Item {
            implicitHeight: 10
            implicitWidth: 200
            Rectangle {
                height: 3
                width: parent.width
                anchors.verticalCenter: parent.verticalCenter
                color: Style.window.color.xdark
                opacity: 0.8
                Rectangle {
                    antialiasing: true
                    color: control.enabled ? Style.window.color.selected : Style.window.color.xlight
                    height: parent.height
                    width: parent.width * (control.value - control.minimumValue) / (control.maximumValue - control.minimumValue)
                }
                Text {
                    anchors.top: parent.bottom
                    anchors.right: parent.right
                    text: control.value.toFixed(2)
                    font.pixelSize: Style.text.size.xsmall
                }
            }
        }
    }

}
