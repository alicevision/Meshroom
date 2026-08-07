import QtQuick
import QtQuick.Controls

import Controls

Rectangle {
    id: root
    required property string label
    required property var attribute
    property bool isLarge
    property bool editable

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
            onEditingFinished: setTextFieldAttribute(root.attribute, text)
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
            Component.onDestruction: {
                if (activeFocus)
                    setTextFieldAttribute(root.attribute, text)
            }
            DropArea {
                enabled: root.editable
                anchors.fill: parent
                onDropped: {
                    if (drop.hasUrls)
                        setTextFieldAttribute(root.attribute, Filepath.urlToString(drop.urls[0]))
                    else if (drop.hasText && drop.text != '')
                        setTextFieldAttribute(root.attribute, drop.text)
                }
            }
        }
    }
}