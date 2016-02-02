import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.2
import ".."
import "."

MenuBar {
    id: root

    style: MenuBarStyle {
        padding {
            left: 8
            right: 8
            top: 0
            bottom: 0
        }
        background: Rectangle {
            color: Style.window.color.xdark
        }
        itemDelegate: Item {
            implicitWidth: childrenRect.width + 16 // left + right padding
            implicitHeight: 30
            Text {
                anchors.verticalCenter: parent.verticalCenter
                horizontalAlignment: Text.AlignHCenter
                color: (styleData.selected || styleData.open) ? Style.text.color.selected : Style.text.color.normal
                text: styleData.text
            }
        }
    }

}
