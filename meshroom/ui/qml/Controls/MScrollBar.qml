import QtQuick
import QtQuick.Controls

/**
 * MScrollBar is a custom scrollbar implementation.
 * It is a vertical scrollbar that can be used to scroll a ListView.
 */

ScrollBar {
    id: root
    policy: ScrollBar.AlwaysOn

    visible: root.horizontal ? parent.contentWidth > parent.width : parent.contentHeight > parent.height
    minimumSize: 0.1

    Component.onCompleted: {
        contentItem.color = Qt.lighter(palette.mid, 2)
    }

    onHoveredChanged: {
        if (pressed) return
        contentItem.color = hovered ? Qt.lighter(palette.mid, 3) : Qt.lighter(palette.mid, 2)
    }

    onPressedChanged: {
        contentItem.color = pressed ? Qt.lighter(palette.mid, 4) : hovered ? Qt.lighter(palette.mid, 3) : Qt.lighter(palette.mid, 2)
    }
}