import QtQuick
import QtQuick.Controls

import Controls

Rectangle {
    id: root
    required property string label
    property bool isLarge
    property bool editable
    signal editingFinished(var text)
    signal destruction(bool activeFocus, var text)
    signal dropped(bool hasUrls, bool hasText, var urlText, var text)
    // Fixed background for the flickable object
    color: palette.base
    width: parent.width
    height: root.isLarge ? 400 : 70
    Flickable {
        width: parent.width
        height: parent.height
        contentWidth: width
        contentHeight: height
        ScrollBar.vertical: MScrollBar {}
        TextArea.flickable: TextArea {
            wrapMode: Text.WordWrap
            padding: 0
            rightPadding: 5
            bottomPadding: 2
            topPadding: 2
            readOnly: !root.editable
            onEditingFinished: root.editingFinished(text)
            text: root.label
            selectByMouse: true
            background: Rectangle {
                visible: errorMessages.length
                border.color: "orange"
                color: "transparent"
                radius: 2
            }
            onPressed: {
                root.forceActiveFocus()
            }
            Component.onDestruction: root.destruction(activeFocus, text)
            DropArea {
                enabled: root.editable
                anchors.fill: parent
                onDropped: (drop) => root.dropped(drop.hasUrls, drop.hasText && drop.text != '', Filepath.urlToString(drop.urls[0]), drop.text)
            }
        }
    }
}