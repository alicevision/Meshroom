import QtQuick
import QtQuick.Controls

import Utils 1.0

/**
 * ColorChart is a color picker based on a set of predefined colors.
 * It takes the form of a ToolButton that pops-up its palette when pressed.
 */

ToolButton {
    id: root

    property var colors: ["red", "green", "blue"]
    property int currentIndex: 0

    signal colorPicked(var colorIndex)

    background: Rectangle {
        color: root.colors[root.currentIndex]
        border.width: hovered ? 1 : 0
        border.color: Colors.sysPalette.midlight
    }

    onPressed: palettePopup.open()

    // Popup for the color palette
    Popup {
        id: palettePopup

        padding: 4
        // Content width is missing side padding (hence the + padding*2)
        implicitWidth: colorChart.contentItem.width + padding * 2

        // Center the current color
        y: -(root.height - padding) / 2
        x: -colorChart.currentItem.x - padding

        // Colors palette
        ListView {
            id: colorChart
            implicitHeight: contentItem.childrenRect.height
            implicitWidth: contentWidth
            orientation: ListView.Horizontal
            spacing: 2
            currentIndex: root.currentIndex
            model: root.colors
            // Display each color as a ToolButton with a custom background
            delegate: ToolButton {
                padding: 0
                width: root.width
                height: root.height
                background: Rectangle {
                    color: modelData
                    // Display border of current/selected item
                    border.width: hovered || index === colorChart.currentIndex ? 1 : 0
                    border.color: Colors.sysPalette.midlight
                }

                onClicked: {
                    colorPicked(index)
                    palettePopup.close()
                }
            }
        }
    }
}
