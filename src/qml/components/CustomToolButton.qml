import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

ToolButton {
    id: root
    property string hoverIconSource: ""
    property int iconSize: _style.icon.size.normal
    style: ButtonStyle {
        panel: Item {
            implicitHeight: root.iconSize
            implicitWidth: root.iconSize
            Image {
                id: icon
                sourceSize: Qt.size(root.iconSize, root.iconSize)
                source: (control.hovered && root.hoverIconSource) ? root.hoverIconSource : control.iconSource
                smooth: true
                opacity: control.hovered ? 0.4 : 1
            }
            Rectangle {
                anchors.centerIn: icon
                width: title.width + 4
                height: parent.height
                color: _style.window.color.xdarker
                opacity: control.hovered ? 0.5 : 0
                visible: control.text.length >= 1
                Behavior on opacity { NumberAnimation{} }
            }
            Text {
                id: title
                Component.onCompleted: width = Math.min(contentWidth, 50)
                anchors.centerIn: icon
                visible: control.hovered
                text: control.text
                font.pixelSize: _style.text.size.xsmall
                color: _style.text.color.normal
                opacity: control.hovered ? 1 : 0
                Behavior on opacity { NumberAnimation{} }
                elide: Text.ElideRight
                wrapMode: Text.WordWrap
                maximumLineCount: 2
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
            }
        }
    }
}
