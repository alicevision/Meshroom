import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Controls 1.0

/**
 * NodeLog displays the log file of Node's chunks (NodeChunks).
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
        property url sourceFile: Filepath.stringToUrl(currentFile)

        sourceComponent: textFileViewerComponent
    }

    Component {
        id: textFileViewerComponent

        TextFileViewer {
            id: textFileViewer
            anchors.fill: parent
            source: componentLoader.sourceFile
            autoReload: root.currentChunk !== undefined && root.currentChunk.statusName === "RUNNING"
        }
    }
}
