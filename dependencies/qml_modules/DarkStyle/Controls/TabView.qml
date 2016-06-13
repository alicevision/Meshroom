import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import ".."
import "."

TabView {

    id: root

    style: TabViewStyle {
        frameOverlap: 0
        tabOverlap: 0
        tab: Rectangle {
            implicitWidth: Math.max(text.width + 4, 50)
            implicitHeight: 30
            color: Style.window.color.xdark
            opacity: styleData.selected ? 1 : 0.6
            Text {
                id: text
                anchors.centerIn: parent
                text: styleData.title
                font.pixelSize: Style.text.size.xsmall
                color: styleData.selected ? Style.text.color.selected : Style.text.color.normal
            }
            Rectangle { // selection indicator
                anchors.left: parent.left
                anchors.bottom: parent.bottom
                width: parent.width
                height: 1
                color: {
                    if(styleData.selected)
                        return Style.window.color.selected;
                    if(styleData.hovered)
                        return Style.window.color.xlight;
                    return Style.window.color.xdark;
                }
            }
            Rectangle { // tab separator
                anchors.right: parent.right
                width: 1
                height: parent.height
                color: Style.window.color.normal
            }
        }
        frame: Item {}
    }

}
