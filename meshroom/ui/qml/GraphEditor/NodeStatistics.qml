import QtQuick 2.11
import QtQuick.Controls 2.3
import QtQuick.Controls 1.4 as Controls1 // SplitView
import QtQuick.Layouts 1.3
import MaterialIcons 2.2
import Controls 1.0
import Utils 1.0

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
    property variant currentChunkIndex
    property variant currentChunk

    SystemPalette { id: activePalette }

    Loader {
        id: componentLoader
        clip: true
        anchors.fill: parent
        property string currentFile: currentChunk ? currentChunk["statisticsFile"] : ""
        property url source: Filepath.stringToUrl(currentFile)

        sourceComponent: chunksLV.chunksSummary ? statViewerComponent : chunkStatViewerComponent
    }

    Component {
        id: chunkStatViewerComponent
        StatViewer {
            id: statViewer
            anchors.fill: parent
            source: componentLoader.source
        }
    }

    Component {
        id: statViewerComponent

        Column {
            spacing: 2
            KeyValue {
                key: "Time"
                property real time: node.elapsedTime
                value: time > 0.0 ? Format.sec2time(time) : "-"
            }
            KeyValue {
                key: "Cumulated Time"
                property real time: node.recursiveElapsedTime
                value: time > 0.0 ? Format.sec2time(time) : "-"
            }
        }
    }
}
