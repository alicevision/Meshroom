import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Controls 1.0
import Utils 1.0

/**
 * NodeStatistics displays statistics data of Node's chunks (NodeChunks).
 *
 * To ease monitoring, it provides periodic auto-reload of the opened file
 * if the related NodeChunk is being computed.
 */

FocusScope {
    id: root

    property variant node
    property variant currentChunkIndex
    property variant currentChunk

    SystemPalette { id: activePalette }

    Loader {
        id: componentLoader
        clip: true
        anchors.fill: parent
        property string currentFile: currentChunk ? currentChunk["statisticsFile"] : ""
        property url sourceFile: Filepath.stringToUrl(currentFile)

        sourceComponent: chunksLV.chunksSummary ? statViewerComponent : chunkStatViewerComponent
    }

    Component {
        id: chunkStatViewerComponent
        StatViewer {
            id: statViewer
            anchors.fill: parent
            source: componentLoader.sourceFile
        }
    }

    Component {
        id: statViewerComponent

        Column {
            spacing: 2
            KeyValue {
                key: "Time"
                property real time: node.elapsedTime
                value: time > 0.0 ? Format.sec2timecode(time) : "-"
            }
            KeyValue {
                key: "Cumulated Time"
                property real time: node.recursiveElapsedTime
                value: time > 0.0 ? Format.sec2timecode(time) : "-"
            }
        }
    }
}
