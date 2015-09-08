import QtQuick 2.2
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.2

Slider {
    id: root
    style: SliderStyle {
        handle: Rectangle {
            width: 15
            height: 15
            radius: height
            antialiasing: true
            color: _style.window.color.selected
        }
        groove: Item {
            implicitHeight: 10
            implicitWidth: 200
            Rectangle {
                height: 3
                width: parent.width
                anchors.verticalCenter: parent.verticalCenter
                color: _style.window.color.xdarker
                opacity: 0.8
                Rectangle {
                    antialiasing: true
                    color: _style.window.color.selected
                    height: parent.height
                    width: parent.width * (control.value - control.minimumValue) / (control.maximumValue - control.minimumValue)
                }
                Text {
                    anchors.top: parent.bottom
                    anchors.right: parent.right
                    text: control.value.toFixed(2)
                    color: _style.text.color.normal
                    elide: Text.ElideRight
                    wrapMode: Text.WrapAnywhere
                    maximumLineCount: 1
                    font.pixelSize: _style.text.size.small
                }
            }
        }
    }
}
