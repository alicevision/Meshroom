import QtQuick
import QtQuick.Controls

import Utils 1.0
import MaterialIcons 2.2

/**
 * ColorSelector is a color picker based on a set of predefined colors.
 * It takes the form of a ToolButton that pops-up its palette when pressed.
 */
MaterialToolButton {
    id: root

    text: MaterialIcons.palette

    // Internal property holding when the popup remains visible and when is it toggled off
    property var isVisible: false

    property var colors: [
                            "#E35C03",
                            "#FFAD7D",
                            "#D0AE22",
                            "#C9C770",
                            "#3D6953",
                            "#79C62F",
                            "#02627E",
                            "#2CB9CC",
                            "#1453E6",
                            "#507DD0",
                            "#4D3E5C",
                            "#A252BD",
                            "#B61518",
                            "#C16162",
                        ]

    // When a color gets selected/choosen
    signal colorSelected(var color)

    // Toggles the visibility of the popup
    onPressed: toggle()

    function toggle() {
        /*
         * Toggles the visibility of the color palette.
         */
        if (!isVisible) {
            palettePopup.open()
            isVisible = true
        }
        else {
            palettePopup.close()
            isVisible = false
        }
    }

    // Popup for the color palette
    Popup {
        id: palettePopup

        // The popup will not get closed unless explicitly closed
        closePolicy: Popup.NoAutoClose

        // Bounds
        padding: 4
        width: (root.height * 4) + (padding * 4)

        // Smart positioning to avoid clipping
        y: -height
        x: {
            // Get the root's position in its parent coordinates
            // This works because mapToItem maps to parent coordinates by default when parent is null
            const parentPos = root.mapToItem(null, 0, 0)
            const parentWidth = root.parent ? root.parent.width : 800 // fallback width
            
            // Calculate space available on left and right
            const spaceOnLeft = parentPos.x
            const spaceOnRight = parentWidth - (parentPos.x + root.width)
            
            // Required space for positioning to the left
            const requiredSpaceLeft = width - root.width - padding
            
            // Check if there's enough space on the left
            if (spaceOnLeft >= requiredSpaceLeft) {
                // Position to the left (original behavior)
                return -width + root.width + padding
            } else if (spaceOnRight >= width + padding) {
                // Position to the right if there's space
                return root.width + padding
            } else {
                // Not enough space on either side, position to minimize clipping
                // If more space on right, align to right edge of button
                if (spaceOnRight > spaceOnLeft) {
                    return root.width + padding
                } else {
                    // Align to left edge of button
                    return -width + root.width + padding
                }
            }
        }

        // Layout of the Colors
        Grid {
            // Allow only 4 columns and all the colors can be adjusted in row multiples of 4
            columns: 4

            spacing: 2
            anchors.centerIn: parent

            // Default -- Reset Colour button
            ToolButton {
                id: defaultButton
                padding: 0
                width: root.height
                height: root.height

                // Emit no color so the graph sets None as the color of the Node
                onClicked: {
                    root.colorSelected("")
                }

                background: Rectangle {
                    color: "#FFFFFF"
                    // display border of current/selected item
                    border.width: defaultButton.hovered ? 1 : 0
                    border.color: "#000000"

                    // Another Rectangle
                    Rectangle {
                        color: "#FF0000"
                        width: parent.width + 8
                        height: 2
                        anchors.centerIn: parent
                        rotation: 135   // Diagonally creating a Red line from bottom left to top right
                    }
                }
            }

            // Colors palette
            Repeater {
                model: root.colors
                // display each color as a ToolButton with a custom background
                delegate: ToolButton {
                    padding: 0
                    width: root.height
                    height: root.height

                    // Emit the model data as the color to update
                    onClicked: {
                        colorSelected(modelData)
                    }

                    // Model color as the background of the button
                    background: Rectangle {
                        color: modelData
                        // display border of current/selected item
                        border.width: hovered ? 1 : 0
                        border.color: "#000000"
                    }
                }
            }
        }
    }
}
