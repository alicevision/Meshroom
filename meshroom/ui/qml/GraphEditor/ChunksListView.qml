import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Utils 1.0
import Node 1.0

/**
 * ChunksListView
 */

ColumnLayout {
    id: root

    property var uigraph: null
    property variant chunks  // Chunks model : list of NodeChunk
    property int currentIndex: 0

    function getCurrentChunkIndex() {
        if ( currentIndex == undefined || !chunks || chunks.length === 0 || currentIndex == ChunkIndexEnum.NULL ) {
            return -1
        }
        let hasPreprocess  = chunks[0].chunkNode.hasPreprocessChunk
        let hasPostprocess  = chunks[0].chunkNode.hasPostprocessChunk
        // Preprocess chunk
        if ( currentIndex == ChunkIndexEnum.PREPROCESS ) {
            return hasPreprocess ? 0 : -1
        }
        // Postprocess chunk
        if ( currentIndex == ChunkIndexEnum.POSTPROCESS ) {
            return hasPostprocess ? chunks.length - 1 : -1
        }
        // Process Chunk
        return currentIndex + (hasPreprocess ? 1 : 0)
    }

    property int currentItemIndex: getCurrentChunkIndex()

    property variant currentChunk: (currentItemIndex >= 0 && chunks && chunks.length > currentItemIndex) ? chunks[currentItemIndex] : undefined

    onChunksChanged: {
        // When the list changes, ensure the current index is in the new range
        if (!chunks)
            currentIndex = ChunkIndexEnum.NULL
        else if (currentIndex >= chunks.length)
            currentIndex = chunks.length-1
    }

    // chunksSummary is in sync with allChunks button (but not directly accessible as it is in a Component)
    property bool chunksSummary: (currentItemIndex === -1)

    width: 60

    ListView {
        id: chunksLV
        Layout.fillWidth: true
        Layout.fillHeight: true

        model: root.chunks

        highlightFollowsCurrentItem: (root.chunksSummary === false)
        keyNavigationEnabled: true
        focus: true
        currentIndex: root.currentIndex
        onCurrentIndexChanged: {
            if (chunksLV.currentIndex !== root.currentIndex) {
                // When the list is resized, the currentIndex is reset to 0.
                // So here we force it to keep the binding.
                chunksLV.currentIndex = Qt.binding(function() { return root.currentIndex })
            }
        }

        header: Component {
            Button {
                id: allChunks
                text: "Chunks"
                width: parent.width
                flat: true
                checkable: true
                property bool summaryEnabled: root.chunksSummary
                checked: summaryEnabled
                onSummaryEnabledChanged: {
                    checked = summaryEnabled
                }
                onClicked: {
                    root.currentIndex = ChunkIndexEnum.NULL
                    checked = true
                }
            }
        }

        delegate: ItemDelegate {
            id: chunkDelegate
            property var chunk: modelData
            text: modelData.chunkIndexName
            highlighted: (currentItemIndex >= 0 && index == currentItemIndex)
            property int chunkIndex: modelData.chunkIndex
            width: ListView.view.width
            leftPadding: 8
            onClicked: {
                chunksLV.forceActiveFocus()
                root.currentIndex = chunkIndex
            }
            Rectangle {
                width: 4
                height: parent.height
                color: Colors.getChunkColor(parent.chunk)
            }
        }
    }

    Connections {
        target: _currentScene
        function onSelectedChunkChanged() {
            for (var i = 0; i < root.chunks.length; i++) {
                if (_currentScene.selectedChunk === root.chunks[i]) {
                    root.currentIndex = i
                    break;
                }
            }
        }
        ignoreUnknownSignals: true
    }
}
