import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import ".."
import "."

ToolButton {

    id: root
    style: ButtonStyle {
        background: Item {
            implicitWidth: 30
            implicitHeight: 30
            opacity: control.enabled ? 0.8: 0.4
            Rectangle {
                anchors.fill: parent
                color: control.checked ? Style.window.color.selected : Style.window.color.light
                opacity: (control.hovered || control.checked) ? 0.8 : 0
                Behavior on opacity { NumberAnimation{} }
            }
            Image {
                anchors.centerIn: parent
                sourceSize: Qt.size(100, 100)
                width: 25
                height: 25
                source: control.iconSource
                smooth: true
                opacity: 0.8
            }
        }
        label: Item {}
    }

}
