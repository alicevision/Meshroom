import QtQuick 2.9
import QtQuick.Controls 2.3
import QtQuick.Controls 1.4 as Controls1 // SplitView
import QtQuick.Layouts 1.3
import MaterialIcons 2.2
import Utils 1.0

import "common.js" as Common

/**
 * NodeLog displays log and statistics data of Node's chunks (NodeChunks)
 *
 * To ease monitoring, it provides periodic auto-reload of the opened file
 * if the related NodeChunk is being computed.
 */
FocusScope {
    property variant node

    SystemPalette { id: activePalette }

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
            currentIndex: 0

            header: Component {
                Label {
                    width: chunksLV.width
                    elide: Label.ElideRight
                    text: "Chunks"
                    padding: 4
                    z: 10
                    background: Rectangle { color: parent.palette.window }
                }
            }

            highlight: Component {
                Rectangle {
                    color: activePalette.highlight
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

            Button {
                text: MaterialIcons.center_focus_strong
                width: parent.width
                visible: (node.globalStatus == "RUNNING" || node.globalStatus == "ERROR") && (node.chunks.count > 1) // only show when node is running or has error and has multiple chunks
                ToolTip.text: node.globalStatus == "ERROR" ? "Select Chunk With Error" : "Select Running Chunk"
                ToolTip.visible: hovered
                font.family: MaterialIcons.fontFamily
                anchors.bottom: chunksLV.bottom
                onClicked: {
                    let chunkIndex = 0;
                    let foundChunk = false;
                    // cycle through the listview until the chunk is found
                    while (!foundChunk) {
                        for(var child in chunksLV.contentItem.children) {
                            // make sure child object is a chunk
                            if (chunksLV.contentItem.children[child].chunk != undefined) {
                                if (chunksLV.contentItem.children[child].chunk.statusName == node.globalStatus) {
                                    chunkIndex = chunksLV.contentItem.children[child].text
                                    foundChunk = true
                                }
                            }
                        }
                        if (!foundChunk) {
                            chunkIndex += 1
                            chunksLV.positionViewAtIndex(chunkIndex, ListView.Visible)
                        }
                    }
                    chunksLV.forceActiveFocus()
                    chunksLV.positionViewAtIndex(chunkIndex, ListView.Beginning)
                    chunksLV.currentIndex = chunkIndex
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
                property string lastLoadedFile
                property date lastModTime
                onCurrentFileChanged: if(visible) loadCurrentFile()
                onVisibleChanged: if(visible) loadCurrentFile()


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
                    background: Rectangle { color: Qt.darker(activePalette.window, 1.2) }
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
                            id: autoRefresh
                            text: MaterialIcons.timer
                            ToolTip.text: "Auto-Refresh when Running"
                            ToolTip.visible: hovered
                            font.family: MaterialIcons.fontFamily
                            checked: true
                            checkable: true
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
                            onClicked: Qt.openUrlExternally(Filepath.stringToUrl(fileSelector.currentFile))
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
                        font.family: "Monospace, Consolas, Monaco"
                    }
                }
            }
        }
    }

    // Auto-reload current file if NodeChunk is being computed
    Timer {
        running: autoRefresh.checked && chunksLV.currentChunk != undefined && chunksLV.currentChunk.statusName === "RUNNING"
        interval: 2000
        repeat: true
        // reload file on start and stop
        onRunningChanged: loadCurrentFile(true)
        onTriggered: loadCurrentFile(true)
    }

    function loadCurrentFile(keepCursorPosition)
    {
        if(keepCursorPosition == undefined)
            keepCursorPosition = false
        var xhr = new XMLHttpRequest;
        xhr.open("GET", Filepath.stringToUrl(fileSelector.currentFile));
        xhr.onreadystatechange = function() {
            if(xhr.readyState == XMLHttpRequest.HEADERS_RECEIVED)
            {
                // if the file is already open
                // check last modification date
                var lastMod = new Date(xhr.getResponseHeader("Last-Modified"));
                if(fileSelector.lastLoadedFile == fileSelector.currentFile
                  && lastMod.getTime() == fileSelector.lastModTime.getTime() )
                {
                    // file has not changed, don't reload it
                    xhr.doLoad = false;
                    return
                }
                // file is different or last modification time has changed
                fileSelector.lastModTime = lastMod
                xhr.doLoad = true
            }
            if (xhr.readyState == XMLHttpRequest.DONE) {
                // store lastLoadedFile url
                fileSelector.lastLoadedFile = fileSelector.currentFile
                // if responseText should not be loaded
                if(!xhr.doLoad)
                {
                    // file could not be opened, reset text and lastModTime
                    if(xhr.status == 0)
                    {
                        fileSelector.lastModTime = new Date()
                        logArea.text = ''
                    }
                    return;
                }
                // store cursor position and content position
                var cursorPosition = logArea.cursorPosition;
                var contentY = logScrollView.ScrollBar.vertical.position;

                // replace text
                logArea.text = xhr.responseText;

                if(autoScroll.checked)
                {
                    // Reset cursor position to trigger scroll to bottom
                    logArea.cursorPosition = 0;
                    logArea.cursorPosition = logArea.length;
                }
                else if(keepCursorPosition)
                {
                    if(cursorPosition)
                        logArea.cursorPosition = cursorPosition;
                    logScrollView.ScrollBar.vertical.position = contentY
                }
            }
        };
        xhr.send();
    }
}
