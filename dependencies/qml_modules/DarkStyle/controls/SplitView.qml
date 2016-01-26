import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import ".."

SplitView {

    id: root

    handleDelegate: Rectangle {
        width: 2
        height: 2
        color: (styleData.hovered || styleData.resizing) ?
                    Style.window.color.normal : Style.window.color.xdark
    }
}
