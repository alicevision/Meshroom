import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import ".."

ScrollView {

    id: root

    style: ScrollViewStyle {
        transientScrollBars: true
        handle: Item {
            implicitWidth: 10
            implicitHeight: 10
            Rectangle {
                color: Style.window.color.xlight
                opacity: 0.8
                anchors.fill: parent
                anchors.margins: 3
            }
        }
        scrollBarBackground: Rectangle {
            implicitWidth: 10
            implicitHeight: 10
            color: Style.window.color.xdark
        }
        incrementControl: Item {}
        decrementControl: Item {}
        corner: Item {}
    }

}
