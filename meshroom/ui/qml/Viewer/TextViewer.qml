import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Controls 1.0
import MaterialIcons 2.2
import Utils 1.0

/**
 * TextViewer displays the content of a text file (e.g. .txt, .json, .log, .csv).
 */

FocusScope {
    id: root

    clip: true

    property url source: ""
    property string fileContent: ""
    property bool loading: false

    // Load the content of the file at the given URL
    function load(url) {
        if (!url || url.toString() === "") {
            fileContent = ""
            return
        }
        root.loading = true
        var xhr = new XMLHttpRequest()
        xhr.open("GET", url, true)
        xhr.onreadystatechange = function() {
            if (xhr.readyState === XMLHttpRequest.DONE) {
                root.fileContent = xhr.responseText
                root.loading = false
            }
        }
        xhr.send()
    }

    onSourceChanged: {
        if (source.toString() !== "") {
            load(source)
        } else {
            fileContent = ""
        }
    }

    Rectangle {
        anchors.fill: parent
        color: Qt.darker(palette.base, 1.1)

        ColumnLayout {
            anchors.fill: parent
            spacing: 0

            // File path toolbar
            RowLayout {
                id: filePathBar
                Layout.fillWidth: true
                spacing: 4
                visible: source.toString() !== ""

                TextField {
                    id: filePathTextField
                    Layout.fillWidth: true
                    text: Filepath.urlToString(root.source)
                    font.pointSize: 8
                    readOnly: true
                    selectByMouse: true
                    background: Item {}
                    padding: 4
                }

                MaterialToolButton {
                    text: MaterialIcons.content_copy
                    ToolTip.text: "Copy File Path to Clipboard"
                    font.pointSize: 10
                    padding: 4
                    onClicked: {
                        filePathTextField.selectAll()
                        filePathTextField.copy()
                        filePathTextField.deselect()
                    }
                }

                MaterialToolButton {
                    text: MaterialIcons.open_in_new
                    ToolTip.text: "Open File Externally"
                    font.pointSize: 10
                    padding: 4
                    onClicked: Qt.openUrlExternally(root.source)
                }
            }

            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: palette.mid
                visible: filePathBar.visible
            }

            // Text area
            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true

                // Loading indicator
                BusyIndicator {
                    anchors.centerIn: parent
                    running: root.loading
                    visible: running
                }

                // Placeholder when no file is loaded
                Label {
                    anchors.centerIn: parent
                    visible: !root.loading && root.source.toString() === ""
                    text: "No file loaded"
                    color: Qt.darker(palette.text, 1.5)
                }

                ScrollView {
                    anchors.fill: parent
                    visible: !root.loading && root.source.toString() !== ""
                    contentWidth: availableWidth

                    TextArea {
                        id: textArea
                        text: root.fileContent
                        readOnly: true
                        wrapMode: TextArea.Wrap
                        font.family: "monospace"
                        font.pointSize: 9
                        selectByMouse: true
                        background: Item {}
                        padding: 8
                    }
                }
            }
        }
    }
}
