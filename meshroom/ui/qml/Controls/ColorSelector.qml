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
                            "#FF6600",
                            "#FFAD7D",
                            "#FFF82F",
                            "#FFFB8B",
                            "#BDFF07",
                            "#E8FF97",
                            "#0BFFCA",
                            "#8EFFF7",
                            "#1158FF",
                            "#77A7FF",
                            "#9318FF",
                            "#EAACFF",
                            "#B61518",
                            "#FF989A",
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

        // center the current color
        y: -height
        x: -width + root.width + padding

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
