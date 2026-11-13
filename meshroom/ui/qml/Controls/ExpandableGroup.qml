import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import MaterialIcons 2.2

/**
 * A custom GroupBox with predefined header that can be hidden and expanded.
 */
GroupBox {
    id: root

    title: ""
    property int sidePadding: 6
    property alias labelBackground: labelBg
    property alias toolBarContent: toolBar.data
    property alias expanded: expandButton.checked

    padding: 2
    leftPadding: sidePadding
    rightPadding: sidePadding
    topPadding: label.height + padding
    background: Item {}

    MouseArea {
        parent: paneLabel
        anchors.fill: parent
        onClicked: function(mouse) {
            expandButton.checked = !expandButton.checked
        }
    }

    label: Pane {
        id: paneLabel
        padding: 2
        width: root.width

        background: Rectangle {
            id: labelBg
            color: palette.window
            opacity: 0.8
        }

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

                MaterialToolButton {
                    id: expandButton
                    ToolTip.text: "Expand More"
                    text: MaterialIcons.expand_more
                    font.pointSize: 10
                    implicitHeight: parent.height
                    checkable: true
                    checked: false
                    // The icon already shows the expanded state: no checked styling
                    textColor: palette.text
                    background: Rectangle {
                        color: !expandButton.enabled ? "transparent" : expandButton.pressed ? Qt.darker(expandButton.palette.base, 1.3) : expandButton.hovered ? Qt.darker(expandButton.palette.base, 0.6) : "transparent"
                    }

                    onCheckedChanged: {
                        if (checked) {
                            ToolTip.text = "Expand Less"
                            text = MaterialIcons.expand_less
                        } else {
                            ToolTip.text = "Expand More"
                            text = MaterialIcons.expand_more
                        }
                    }
                }
            }
        }
    }
}
