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
            }

            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: palette.mid
                visible: filePathBar.visible
            }

            // Text content area
            TextFileViewer {
                Layout.fillWidth: true
                Layout.fillHeight: true
                source: root.source
            }
        }
    }
}
