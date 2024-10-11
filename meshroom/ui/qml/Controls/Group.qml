import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

/**
 * A custom GroupBox with predefined header.
 */
GroupBox {
    id: root

    title: ""
    property int sidePadding: 6
    property alias labelBackground: labelBg
    property alias toolBarContent: toolBar.data

    padding: 2
    leftPadding: sidePadding
    rightPadding: sidePadding
    topPadding: label.height + padding
    background: Item {}

    label: Pane {
        background: Rectangle {
            id: labelBg
            color: palette.base
            opacity: 0.8
        }
        padding: 2
        width: root.width
        RowLayout {
            width: parent.width
            Label {
                text: root.title
                Layout.fillWidth: true
                elide: Text.ElideRight
                padding: 3
                font.bold: true
                font.pointSize: 8
            }
            RowLayout {
                id: toolBar
                height: parent.height
            }
        }
    }
}
