import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.11
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
    property bool expanded: expandButton.checked

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

            MouseArea {
                anchors.fill: parent
                onClicked: {
                    expandButton.checked = !expandButton.checked
                }
            }
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

                MaterialToolButton {
                    id: expandButton
                    ToolTip.text: "Expand More"
                    text: MaterialIcons.expand_more
                    font.pointSize: 10
                    implicitHeight: parent.height
                    checkable: true
                    checked: false

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
