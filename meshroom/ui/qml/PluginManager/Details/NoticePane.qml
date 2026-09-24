import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import MaterialIcons 2.2

/**
 * NoticePane is a bordered box with an icon + title header.
 */

Pane {
    id: root
    padding: 8

    property string title: ""
    property string text: ""
    property string icon: MaterialIcons.error_outline

    background: Rectangle {
        color: "transparent"
        border.color: palette.mid
        radius: 4
    }

    contentItem: ColumnLayout {
        spacing: 10

        // Header
        RowLayout {
            Layout.fillWidth: true
            spacing: 6

            // Icon
            Label {
                text: root.icon
                font.family: MaterialIcons.fontFamily
                font.pointSize: 13
                color: Qt.darker(palette.text, 1.175)
            }

            // Title
            Label {
                text: root.title
                Layout.fillWidth: true
                color: Qt.darker(palette.text, 1.175)
            }
        }

        // Body Text
        Label {
            text: root.text
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }
    }
}
