import QtQuick 2.2
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.2

TableView {
    id: root
    style: TableViewStyle {
        transientScrollBars: true
        frame: Rectangle {
            color: _style.window.color.xdarker
            border.color: _style.window.color.xdarker
            border.width: 2
        }
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
