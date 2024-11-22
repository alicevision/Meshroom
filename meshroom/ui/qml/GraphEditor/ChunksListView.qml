import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import "common.js" as Common

/**
 * ChunkListView
 */

ColumnLayout {
    id: root
    property variant chunks
    property int currentIndex: 0
    property variant currentChunk: (chunks && currentIndex >= 0) ? chunks.at(currentIndex) : undefined

    onChunksChanged: {
        // When the list changes, ensure the current index is in the new range
        if (currentIndex >= chunks.count)
            currentIndex = chunks.count-1
    }

    // chunksSummary is in sync with allChunks button (but not directly accessible as it is in a Component)
    property bool chunksSummary: (currentIndex === -1)

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
                    root.currentIndex = -1
                    checked = true
                }
            }
        }
        highlight: Component {
            Rectangle {
                visible: true  // !root.chunksSummary
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
            width: ListView.view.width
            leftPadding: 8
            onClicked: {
                chunksLV.forceActiveFocus()
                root.currentIndex = index
            }
            Rectangle {
                width: 4
                height: parent.height
                color: Common.getChunkColor(parent.chunk)
            }
        }
    }
}
