import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import MaterialIcons 2.2

/**
 * Node Badge to inform about compatibility issues
 * Provides 2 delegates (can be set using sourceComponent property):
 *     - iconDelegate (default): icon + tooltip with information about the issue
 *     - bannerDelegate: banner with issue info + upgrade request button
 */

Loader {
    id: root

    property bool canUpgrade
    property string issueDetails
    property color color: canUpgrade ? "#E68A00" : "#F44336"

    signal upgradeRequest()

    sourceComponent: iconDelegate

    property Component iconDelegate: Component {

        Label {
            text: MaterialIcons.warning
            font.family: MaterialIcons.fontFamily
            font.pointSize: 12
            color: root.color

            MouseArea {
                anchors.fill: parent
                hoverEnabled: true
                onPressed: mouse.accepted = false
                ToolTip.text: issueDetails
                ToolTip.visible: containsMouse
            }
        }
    }

    property Component bannerDelegate: Component {

        Pane {
            padding: 6
            clip: true
            background: Rectangle { color: root.color }

            RowLayout {
                width: parent.width
                Column {
                    Layout.fillWidth: true
                    Label {
                        width: parent.width
                        elide: Label.ElideMiddle
                        font.bold: true
                        text: "Compatibility issue"
                        color: "white"
                    }
                    Label {
                        width: parent.width
                        elide: Label.ElideMiddle
                        text: root.issueDetails
                        color: "white"
                    }
                }
                Button {
                    visible: root.canUpgrade && (parent.width > width) ? 1 : 0
                    palette.window: root.color
                    palette.button: Qt.darker(root.color, 1.2)
                    palette.buttonText: "white"
                    text: "Upgrade"
                    onClicked: upgradeRequest()
                }
            }
        }
    }
}
