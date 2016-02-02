import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.2
import ".."
import "."

Button {

    id: root
    style: ButtonStyle {
        padding {
            top: 0
            left: (control.iconSource != "") ? 25 : 4
            right: 4
            bottom: 0
        }
        background: Item {
            implicitHeight: 30
            Rectangle {
                anchors.fill: parent
                color: Style.window.color.light
                opacity: control.hovered ? 0.8 : 0
                Behavior on opacity { NumberAnimation {} }
            }
            Image {
                anchors.verticalCenter: parent.verticalCenter
                visible: control.iconSource != ""
                sourceSize: Qt.size(25, 25)
                source: control.iconSource
                smooth: true
                opacity: 0.8
            }
        }
        label: Text {
            text: control.text
            font.pixelSize: Style.text.size.small
            color: control.hovered ? Style.text.color.light : Style.text.color.normal
            horizontalAlignment: Text.AlignHCenter
        }
    }

}
