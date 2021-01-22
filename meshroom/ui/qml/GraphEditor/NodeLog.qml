import QtQuick 2.11
import QtQuick.Controls 2.3
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
    property int currentChunkIndex
    property variant currentChunk

    Layout.fillWidth: true
    Layout.fillHeight: true

    SystemPalette { id: activePalette }

    Loader {
        id: componentLoader
        clip: true
        anchors.fill: parent

        property string currentFile: (root.currentChunkIndex >= 0 && root.currentChunk) ? root.currentChunk["logFile"] : ""
        property url source: Filepath.stringToUrl(currentFile)

        sourceComponent: textFileViewerComponent
    }

    Component {
        id: textFileViewerComponent

        TextFileViewer {
            id: textFileViewer
            anchors.fill: parent
            source: componentLoader.source
            autoReload: root.currentChunk !== undefined && root.currentChunk.statusName === "RUNNING"
            // source is set in fileSelector
        }
    }
}
