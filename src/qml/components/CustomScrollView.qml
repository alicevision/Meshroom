import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

ScrollView {
    id: root
    style: ScrollViewStyle {
        transientScrollBars: true
        handle: Item {
            implicitWidth: 10
            implicitHeight: 10
            Rectangle {
                color: _style.window.color.xlighter
                opacity: 0.8
                anchors.fill: parent
                anchors.margins: 3
            }
        }
        scrollBarBackground: Rectangle {
            implicitWidth: 10
            implicitHeight: 10
            color: _style.window.color.xdarker
        }
        incrementControl: Item {}
        decrementControl: Item {}
        corner: Item {}
    }
}
