import QtQuick 2.2
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.3

ToolButton {
    id: root
    property string hoverIconSource: ""
    property int iconSize: _style.icon.size.normal
    property int margin: 10
    style: ButtonStyle {
        panel: Item
        {
            implicitHeight: root.iconSize + root.margin
            implicitWidth: root.iconSize + root.margin
            Image {
                anchors.centerIn: parent
                sourceSize: Qt.size(root.iconSize, root.iconSize)
                smooth: true
                source: (control.hovered && root.hoverIconSource) ? root.hoverIconSource : control.iconSource
            }
        }
    }
}
