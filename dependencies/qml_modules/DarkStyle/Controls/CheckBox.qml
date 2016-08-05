import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Controls.Private 1.0
import ".."
import "."

CheckBox {
    style: CheckBoxStyle {
        indicator: Rectangle {
            implicitWidth: 16
            implicitHeight: 16
            color: Style.window.color.xdark
            Rectangle {
                anchors.fill: parent
                visible: control.checked
                color: Style.window.color.selected
                anchors.margins: 2
            }
        }
        label: Text {
            text: control.text
        }
    }
}
