import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Controls 1.0

import "common.js" as Common

/**
 * Displays Node documentation
 */

FocusScope {
    id: root

    property variant node

    SystemPalette { id: activePalette }

    ScrollView {
        width: parent.width
        height: parent.height
        ScrollBar.vertical.policy: ScrollBar.AlwaysOn
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
        clip: true

        TextEdit {
            width: parent.parent.width
            height: parent.height

            padding: 8
            textFormat: TextEdit.MarkdownText
            selectByMouse: true
            selectionColor: activePalette.highlight
            color: activePalette.text
            text: node ? node.documentation : ""
            wrapMode: TextEdit.Wrap
        }
    }
}
