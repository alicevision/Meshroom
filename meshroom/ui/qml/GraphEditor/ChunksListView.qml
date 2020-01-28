import QtQuick 2.11
import QtQuick.Controls 2.3
import QtQuick.Controls 1.4 as Controls1 // SplitView
import QtQuick.Layouts 1.3
import MaterialIcons 2.2
import Controls 1.0

import "common.js" as Common

/**
 * ChunkListView
 */
ListView {
    id: chunksLV

    // model: node.chunks

    property variant currentChunk: currentItem ? currentItem.chunk : undefined

    width: 60
    Layout.fillHeight: true
    highlightFollowsCurrentItem: true
    keyNavigationEnabled: true
    focus: true
    currentIndex: 0

    signal changeCurrentChunk(int chunkIndex)

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
            chunksLV.changeCurrentChunk(index)
        }
        Rectangle {
            width: 4
            height: parent.height
            color: Common.getChunkColor(parent.chunk)
        }
    }
}
