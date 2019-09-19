import QtQuick 2.11
import QtQuick.Controls 2.3
import QtQuick.Controls 1.4 as Controls1 // SplitView
import QtQuick.Layouts 1.3
import MaterialIcons 2.2
import Controls 1.0

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
                onCurrentFileChanged: {
                    // only set text file viewer source when ListView is fully ready
                    // (either empty or fully populated with a valid currentChunk)
                    // to avoid going through an empty url when switching between two nodes

                    if(!chunksLV.count || chunksLV.currentChunk)
                        logComponentLoader.source = Filepath.stringToUrl(currentFile);

                }

                TabButton {
                    property string fileProperty: "logFile"
                    text: "Output"
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

            Loader {
                id: logComponentLoader
                clip: true
                Layout.fillWidth: true
                Layout.fillHeight: true
                property url source
                sourceComponent: fileSelector.currentItem.fileProperty === "statisticsFile" ? statViewerComponent : textFileViewerComponent
            }

            Component {
                id: textFileViewerComponent
                TextFileViewer {
                    id: textFileViewer
                    source: logComponentLoader.source
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    autoReload: chunksLV.currentChunk !== undefined && chunksLV.currentChunk.statusName === "RUNNING"
                    // source is set in fileSelector
                }
            }

            Component {
                id: statViewerComponent
                StatViewer {
                    id: statViewer
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    source: logComponentLoader.source
                }
            }
        }
    }
}
