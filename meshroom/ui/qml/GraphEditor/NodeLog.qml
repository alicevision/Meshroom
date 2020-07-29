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
    id: root
    property variant node
    property alias chunkCurrentIndex: chunksLV.currentIndex
    signal changeCurrentChunk(int chunkIndex)

    SystemPalette { id: activePalette }

    Controls1.SplitView {
        anchors.fill: parent

        // The list of chunks
        ChunksListView {
            id: chunksLV
            Layout.fillHeight: true
            model: node.chunks
            onChangeCurrentChunk: root.changeCurrentChunk(chunkIndex)
        }

        Loader {
            id: componentLoader
            clip: true
            Layout.fillWidth: true
            Layout.fillHeight: true
            property url source

            property string currentFile: chunksLV.currentChunk ? chunksLV.currentChunk["logFile"] : ""
            onCurrentFileChanged: {
                // only set text file viewer source when ListView is fully ready
                // (either empty or fully populated with a valid currentChunk)
                // to avoid going through an empty url when switching between two nodes

                if(!chunksLV.count || chunksLV.currentChunk)
                    componentLoader.source = Filepath.stringToUrl(currentFile);

            }

            sourceComponent: textFileViewerComponent
        }

        Component {
            id: textFileViewerComponent
            TextFileViewer {
                id: textFileViewer
                source: componentLoader.source
                Layout.fillWidth: true
                Layout.fillHeight: true
                autoReload: chunksLV.currentChunk !== undefined && chunksLV.currentChunk.statusName === "RUNNING"
                // source is set in fileSelector
            }
        }
    }
}
