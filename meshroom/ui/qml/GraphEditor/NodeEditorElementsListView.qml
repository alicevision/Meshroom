import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls 1.4 as Controls1 // SplitView
import QtQuick.Layouts 1.11
import MaterialIcons 2.2
import Controls 1.0

import "common.js" as Common

/**
 * NodeEditorElementsListView
 */
ColumnLayout {
    id: root
    property variant elements
    property int currentIndex: 0
    property bool isChunk: true
    property string title: "Chunks"

    // TODO : change to currentElement
    property variant currentElement: (elements && currentIndex >= 0) ? elements.at(currentIndex) : undefined

    onElementsChanged: {
        // When the list changes, ensure the current index is in the new range
        if (currentIndex >= elements.count)
            currentIndex = elements.count-1
    }

    // elementsSummary is in sync with allElements button (but not directly accessible as it is in a Component)
    property bool elementsSummary: (currentIndex === -1)

    width: 75

    ListView {
        id: elementsLV
        Layout.fillWidth: true
        Layout.fillHeight: true

        model: root.elements

        highlightFollowsCurrentItem: (root.elementsSummary === false)
        keyNavigationEnabled: true
        focus: true
        currentIndex: root.currentIndex
        onCurrentIndexChanged: {
            if (elementsLV.currentIndex !== root.currentIndex) {
                // When the list is resized, the currentIndex is reset to 0.
                // So here we force it to keep the binding.
                elementsLV.currentIndex = Qt.binding(function() { return root.currentIndex })
            }
        }

        header: Component {
            Button {
                id: allElements
                text: title
                width: parent.width
                flat: true
                checkable: true
                property bool summaryEnabled: root.elementsSummary
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
                visible: true  // !root.elementsSummary
                color: activePalette.highlight
                opacity: 0.3
                z: 2
            }
        }
        highlightMoveDuration: 0
        highlightResizeDuration: 0

        delegate: ItemDelegate {
            id: elementDelegate
            property var element: object
            text: index
            width: parent ? parent.width : 0
            leftPadding: 8
            onClicked: {
                elementsLV.forceActiveFocus()
                root.currentIndex = index
            }
            Rectangle {
                width: 4
                height: parent.height
                color: isChunk ? Common.getChunkColor(parent.element) : palette.mid
            }
        }
    }
}
