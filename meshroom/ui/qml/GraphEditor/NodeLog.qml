import QtQuick 2.9
import QtQuick.Controls 2.3
import QtQuick.Controls 1.4 as Controls1 // SplitView
import QtQuick.Layouts 1.3
import MaterialIcons 2.2
import "common.js" as Common

/**
 * NodeLog displays log and statistics data of Node's chunks (NodeChunks)
 *
 * To ease monitoring, it provides periodic auto-reload of the opened file
 * if the related NodeChunk is being computed.
 */
FocusScope {
    property variant node

    SystemPalette { id: palette }

    Controls1.SplitView {
        anchors.fill: parent

        // The list of chunks
        ListView {
            id: chunksLV

            property variant currentChunk: currentItem ? currentItem.chunk : undefined

            width: 60
            Layout.fillHeight: true
            model: node.chunks
            highlightFollowsCurrentItem: true
            keyNavigationEnabled: true
            focus: true
            currentIndex: -1

            header: Component {
                Label {
                    width: chunksLV.width
                    elide: Label.ElideRight
                    text: "Chunks"
                    padding: 4
                    z: 10
                    background: Rectangle { color: palette.window }
                }
            }

            highlight: Component {
                Rectangle {
                    color: palette.highlight
                    opacity: 0.3
                    z: 2
                }
            }
            highlightMoveDuration: 0
            highlightResizeDuration: 0

            delegate: ItemDelegate {
                id: chunkDelegate
                property var chunk: object
                text: index
                width: parent.width
                leftPadding: 8
                onClicked: {
                    chunksLV.forceActiveFocus()
                    chunksLV.currentIndex = index
                }
                Rectangle {
                    width: 4
                    height: parent.height
                    color: Common.getChunkColor(parent.chunk)
                }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.margins: 1

            spacing: 1

            TabBar {
                id: fileSelector
                Layout.fillWidth: true
                property string currentFile: chunksLV.currentChunk ? chunksLV.currentChunk[currentItem.fileProperty] : ""
                onCurrentFileChanged: if(visible) loadCurrentFile(false)
                onVisibleChanged: loadCurrentFile()

                TabButton {
                    property string fileProperty: "logFile"
                    text: "Log"
                    padding: 4
                }
                TabButton {
                    property string fileProperty: "statisticsFile"
                    text: "Statistics"
                    padding: 4
                }
                TabButton {
                    property string fileProperty: "statusFile"
                    text: "Status"
                    padding: 4
                }
            }

            RowLayout {
                Layout.fillHeight: true
                Layout.fillWidth: true
                spacing: 0
                Pane {
                    id: tb
                    Layout.alignment: Qt.AlignTop
                    Layout.fillHeight: true
                    padding: 0
                    background: Rectangle { color: Qt.darker(palette.window, 1.2) }
                    Column {
                        height: parent.height
                        ToolButton {
                            text: MaterialIcons.refresh
                            ToolTip.text: "Refresh"
                            ToolTip.visible: hovered
                            font.family: MaterialIcons.fontFamily
                            onClicked: loadCurrentFile(false)
                        }
                        ToolButton {
                            text: MaterialIcons.vertical_align_top
                            ToolTip.text: "Scroll to Top"
                            ToolTip.visible: hovered
                            font.family: MaterialIcons.fontFamily
                            onClicked: logArea.cursorPosition = 0
                        }
                        ToolButton {
                            text: MaterialIcons.vertical_align_bottom
                            ToolTip.text: "Scroll to Bottom"
                            ToolTip.visible: hovered
                            font.family: MaterialIcons.fontFamily
                            onClicked: logArea.cursorPosition = logArea.length
                        }
                        ToolButton {
                            id: autoScroll
                            text: MaterialIcons.system_update_alt
                            ToolTip.text: "Auto-Scroll to Bottom"
                            ToolTip.visible: hovered
                            font.family: MaterialIcons.fontFamily
                            checkable: true
                            checked: true
                        }
                        ToolButton {
                            text: MaterialIcons.open_in_new
                            ToolTip.text: "Open Externally"
                            ToolTip.visible: hovered
                            font.family: MaterialIcons.fontFamily
                            enabled: fileSelector.currentFile != ""
                            onClicked: Qt.openUrlExternally(fileSelector.currentFile)
                        }
                    }
                }
                // Log display
                ScrollView {
                    id: logScrollView
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    TextArea {
                        id: logArea
                        selectByMouse: true
                        selectByKeyboard: true
                        persistentSelection: true
                    }
                }
            }
        }
    }

    // Auto-reload current file if NodeChunk is being computed
    Timer {
        running: chunksLV.currentChunk != undefined && chunksLV.currentChunk.statusName === "RUNNING"
        interval: 2000
        repeat: true
        triggeredOnStart: true
        onTriggered: loadCurrentFile(true)
    }

    function loadCurrentFile(keepCursorPosition)
    {
        var xhr = new XMLHttpRequest;
        xhr.open("GET", fileSelector.currentFile);
        xhr.onreadystatechange = function() {
            if (xhr.readyState == XMLHttpRequest.DONE) {
                var cursorPosition = logArea.cursorPosition;
                logArea.text = xhr.responseText;
                // Reset cursor position to trigger scroll to bottom
                logArea.cursorPosition = 0;
                if(autoScroll.checked)
                {
                    logArea.cursorPosition = logArea.length;
                }
                else if(keepCursorPosition)
                {
                    logArea.cursorPosition = cursorPosition;
                }
            }
        };
        xhr.send();
    }
}
