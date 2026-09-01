import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

RowLayout {
    id: root
    required property string text
    required property bool mandatory
    property bool editable
    signal editingFinished(var text)
    signal accepted(var parameterLabel, var text)
    signal destruction(bool activeFocus, var text)
    signal dropped(bool hasUrls, bool hasText, var urlText, var text)
    signal triggered(var text, int start, int end, int length, var clipboard)
    anchors.fill: parent
    TextField {
        id: textField
        Layout.fillWidth: true
        readOnly: !root.editable
        text: root.text.trim()
        placeholderText: root.mandatory ? "This field is required" : ""
        placeholderTextColor: "gray"
        // Don't disable the component to keep interactive features (text selection, context menu...).
        // Only override the look by using the Disabled palette.
        SystemPalette {
            id: disabledPalette
            colorGroup: SystemPalette.Disabled
        }
        background: Rectangle {
            border.color: errorMessages.length ? "orange" : "transparent"
            color:  Qt.darker(palette.window, 1.2)
            radius: 2
        }
        states: [
            State {
                when: readOnly
                PropertyChanges {
                    target: textField
                    color: disabledPalette.text
                }
            }
        ]
        selectByMouse: true
        persistentSelection: false
        onEditingFinished: root.editingFinished(text)

        onAccepted: root.accepted(parameterLabel, text)
        Keys.onPressed: function(event) {
            if ((event.key == Qt.Key_Escape)) {
                event.accepted = true
                parameterLabel.forceActiveFocus()
            }
        }
        Component.onDestruction: root.destruction(activeFocus, text)
        DropArea {
            enabled: root.editable
            anchors.fill: parent
            onDropped: (drop) => root.dropped(drop.hasUrls, drop.hasText && drop.text != '', Filepath.urlToString(drop.urls[0]), drop.text)
        }
        onPressed: (event) => {
            if (event.button == Qt.RightButton) {
                // Keep selection persistent while context menu is open to
                // visualize what is being copied or what will be replaced on paste.
                persistentSelection = true
                const menu = textFieldMenuComponent.createObject(textField)
                menu.popup()
                if (selectedText === "") {
                    cursorPosition = positionAt(event.x, event.y)
                }
            }
        }
        Component {
            id: textFieldMenuComponent
            Menu {
                onOpened: {
                    // Keep cursor visible to see where pasting would happen.
                    textField.cursorVisible = true
                }
                onClosed: {
                    // Disable selection persistency behavior once menu is closed and
                    // give focus back to the parent TextField.
                    textField.persistentSelection = false
                    textField.forceActiveFocus()
                    destroy()
                }
                MenuItem {
                    text: "Copy"
                    enabled: root.text != ""
                    onTriggered: {
                        const hasSelection = textField.selectionStart !== textField.selectionEnd
                        if (hasSelection) {
                            // Use `TextField.copy` to copy only the current selection.
                            textField.copy()
                        }
                        else {
                            Clipboard.setText(root.text)
                        }
                    }
                }
                MenuItem {
                    text: "Paste"
                    enabled: !readOnly
                    onTriggered: {
                        const clipboardText = Clipboard.getText()
                        if (clipboardText.length === 0) {
                            return
                        }
                        triggered(textField.text, textField.selectionStart, textField.selectionEnd, textField.text.length, clipboardText)
                    }
                }
            }
        }
    }
}