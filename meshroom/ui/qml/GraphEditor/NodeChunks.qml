import QtQuick

import Utils 1.0

ListView {
    id: root
    interactive: false
    property bool highlightChunks: true

    SystemPalette { id: activePalette }

    property var targetNode: null

    // Pre/Post process chunk objects (single items)
    property var preprocessChunk: null
    property var postprocessChunk: null

    property color defaultColor: Qt.darker(activePalette.window, 1.1)
    property real chunkHeight: height
    property int modelSize: model ? model.count : 0
    
    // Account for header/footer in width calculations
    property bool hasHeader: preprocessChunk !== null
    property bool hasFooter: postprocessChunk !== null
    property int totalChunks: modelSize + (hasHeader ? 1 : 0) + (hasFooter ? 1 : 0)
    
    property bool modelIsBig: (3 * totalChunks >= width)
    property real chunkWidth: {
        if (totalChunks == 0) return 0
        return (width / totalChunks) - spacing
    }

    orientation: ListView.Horizontal

    // If we have enough space, add one pixel margin between chunks
    spacing: modelIsBig ? 0 : 1

    // Header: Preprocess chunk
    header: Loader {
        active: root.hasHeader
        visible: active
        
        sourceComponent: Rectangle {
            height: root.chunkHeight
            width: root.chunkWidth
            
            property var chunkColor: Colors.getChunkColor(root.preprocessChunk, { "NONE": root.defaultColor })
            color: {
                if (!root.highlightChunks || root.totalChunks == 1)
                    return chunkColor
                // Index 0 for header
                return Qt.lighter(chunkColor, 1.1)
            }
        }
    }

    // Main delegate for chunks list
    delegate: Rectangle {
        id: chunkDelegate
        height: root.chunkHeight
        width: root.chunkWidth
        
        property var chunkColor: Colors.getChunkColor(object, { "NONE": root.defaultColor })
        color: {
            if (!root.highlightChunks || root.totalChunks == 1)
                return chunkColor
            
            // Offset index by 1 if we have a header for alternating colors
            var effectiveIndex = root.hasHeader ? index + 1 : index
            if (effectiveIndex % 2 == 0)
                return Qt.lighter(chunkColor, 1.1)
            else
                return Qt.darker(chunkColor, 1.1)
        }
    }

    // Footer: Postprocess chunk
    footer: Loader {
        active: root.hasFooter
        visible: active
        
        sourceComponent: Rectangle {
            height: root.chunkHeight
            width: root.chunkWidth
            
            property var chunkColor: Colors.getChunkColor(root.postprocessChunk, { "NONE": root.defaultColor })
            color: {
                if (!root.highlightChunks || root.totalChunks == 1)
                    return chunkColor
                
                // Calculate effective index for alternating colors
                var effectiveIndex = root.modelSize + (root.hasHeader ? 1 : 0)
                if (effectiveIndex % 2 == 0)
                    return Qt.lighter(chunkColor, 1.1)
                else
                    return Qt.darker(chunkColor, 1.1)
            }
        }
    }
}