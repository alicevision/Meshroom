import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Controls 1.0
import MaterialIcons 2.2

/**
 * NodeTypeBrowser displays a panel listing node categories and nodes.
 * Selecting a category shows the nodes in that category.
 * Selecting a node shows its documentation.
 * Double-clicking a node creates it in the graph.
 */

Panel {
    id: root

    /// The node types model ({nodeType: {category, documentation}, ...})
    property variant nodeTypesModel: null

    /// Currently selected node type name
    property string selectedNodeName: ""

    /// Signal emitted when a node type should be created
    signal nodeTypeDoubleClicked(string nodeType)

    title: "Node Types"
    clip: true

    SystemPalette { id: activePalette }

    /// Lower-cased search filter text (sourced from the header SearchBar)
    readonly property string filterText: searchBar.text.toLowerCase()

    /// True when the search bar contains a non-empty query
    readonly property bool hasActiveFilter: filterText !== ""

    // SearchBar placed in the panel header, matching the ImageGallery pattern
    headerBar: RowLayout {
        SearchBar {
            id: searchBar
            toggle: true
            maxWidth: 150
            onTextChanged: searchDebounce.restart()
        }
    }

    // Debounce timer: avoids re-filtering on every keystroke
    Timer {
        id: searchDebounce
        interval: 150
        onTriggered: root.selectFirstCategory()
    }

    /// Returns plain text with occurrences of searchTerm wrapped in a blue <font> tag.
    /// The input plainText is HTML-escaped before substitution.
    function highlightText(plainText, searchTerm) {
        if (!searchTerm || searchTerm === "")
            return plainText
        var escaped = plainText
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
        var lowerEscaped = escaped.toLowerCase()
        var result = ""
        var pos = 0
        while (pos < escaped.length) {
            var idx = lowerEscaped.indexOf(searchTerm, pos)
            if (idx < 0) {
                result += escaped.substring(pos)
                break
            }
            result += escaped.substring(pos, idx)
            result += "<font color='" + activePalette.highlight + "'>" + escaped.substring(idx, idx + searchTerm.length) + "</font>"
            pos = idx + searchTerm.length
        }
        return result
    }

    /// Returns true if the given node name matches the current filter
    function nodeMatchesFilter(name) {
        if (filterText === "")
            return true
        if (name.toLowerCase().indexOf(filterText) >= 0)
            return true
        var info = nodeTypesModel ? nodeTypesModel[name] : null
        if (info && info["documentation"] &&
                info["documentation"].toLowerCase().indexOf(filterText) >= 0)
            return true
        return false
    }

    /// Compute a sorted list of categories that have at least one matching node
    function getCategories() {
        if (!nodeTypesModel)
            return []
        var cats = {}
        for (var name in nodeTypesModel) {
            if (!nodeMatchesFilter(name))
                continue
            var cat = nodeTypesModel[name]["category"]
            if (!cats[cat])
                cats[cat] = true
        }
        return Object.keys(cats).sort()
    }

    /// Get sorted, filtered node names for a given category
    function getNodesForCategory(category) {
        if (!nodeTypesModel)
            return []
        var nodes = []
        for (var name in nodeTypesModel) {
            if (nodeTypesModel[name]["category"] === category && nodeMatchesFilter(name))
                nodes.push(name)
        }
        return nodes.sort()
    }

    /// Select the first available category and its first node
    function selectFirstCategory() {
        var cats = getCategories()
        if (cats.length === 0) {
            categoryList.currentIndex = -1
            nodeList.currentIndex = -1
            root.selectedNodeName = ""
            return
        }
        categoryList.currentIndex = 0
        Qt.callLater(function() {
            if (nodeList.count > 0) {
                nodeList.currentIndex = 0
                root.selectedNodeName = nodeList.model[0]
            } else {
                nodeList.currentIndex = -1
                root.selectedNodeName = ""
            }
        })
    }

    onVisibleChanged: {
        if (visible)
            selectFirstCategory()
    }

    MSplitView {
        anchors.fill: parent

        // Left column: categories
        Rectangle {
            SplitView.preferredWidth: 120
            SplitView.minimumWidth: 60
            color: Qt.darker(activePalette.window, 1.05)

            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                Label {
                    text: "Categories"
                    font.bold: true
                    padding: 6
                    Layout.fillWidth: true
                    background: Rectangle { color: Qt.darker(activePalette.window, 1.15) }
                }

                ListView {
                    id: categoryList
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    model: root.getCategories()
                    currentIndex: -1

                    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

                    delegate: ItemDelegate {
                        width: categoryList.width
                        height: 28
                        highlighted: categoryList.currentIndex === index
                        padding: 6

                        contentItem: Label {
                            text: modelData
                            elide: Text.ElideRight
                            verticalAlignment: Text.AlignVCenter
                        }

                        background: Rectangle {
                            color: parent.highlighted
                                   ? activePalette.highlight
                                   : (parent.hovered ? Qt.darker(activePalette.window, 1.2) : "transparent")
                        }

                        onClicked: {
                            categoryList.currentIndex = index
                            Qt.callLater(function() {
                                if (nodeList.count > 0) {
                                    nodeList.currentIndex = 0
                                    root.selectedNodeName = nodeList.model[0]
                                } else {
                                    nodeList.currentIndex = -1
                                    root.selectedNodeName = ""
                                }
                            })
                        }
                    }
                }
            }
        }

        // Middle column: nodes in selected category
        Rectangle {
            SplitView.preferredWidth: 140
            SplitView.minimumWidth: 60
            color: activePalette.window

            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                Label {
                    text: "Nodes"
                    font.bold: true
                    padding: 6
                    Layout.fillWidth: true
                    background: Rectangle { color: Qt.darker(activePalette.window, 1.15) }
                }

                ListView {
                    id: nodeList
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    currentIndex: -1

                    model: categoryList.currentIndex >= 0
                           ? root.getNodesForCategory(root.getCategories()[categoryList.currentIndex])
                           : []

                    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

                    delegate: ItemDelegate {
                        width: nodeList.width
                        height: 28
                        highlighted: nodeList.currentIndex === index
                        padding: 6

                        contentItem: Label {
                            textFormat: root.hasActiveFilter ? Text.RichText : Text.AutoText
                            text: root.hasActiveFilter
                                  ? root.highlightText(modelData, root.filterText)
                                  : modelData
                            elide: Text.ElideRight
                            verticalAlignment: Text.AlignVCenter
                        }

                        background: Rectangle {
                            color: parent.highlighted
                                   ? activePalette.highlight
                                   : (parent.hovered ? Qt.darker(activePalette.window, 1.2) : "transparent")
                        }

                        onClicked: {
                            nodeList.currentIndex = index
                            root.selectedNodeName = modelData
                        }

                        onDoubleClicked: {
                            root.nodeTypeDoubleClicked(modelData)
                        }

                        Keys.onReturnPressed: root.nodeTypeDoubleClicked(modelData)
                        Keys.onEnterPressed: root.nodeTypeDoubleClicked(modelData)
                    }
                }
            }
        }

        // Right column: node documentation
        Rectangle {
            SplitView.fillWidth: true
            SplitView.minimumWidth: 100
            color: activePalette.window

            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                Label {
                    text: "Documentation"
                    font.bold: true
                    padding: 6
                    Layout.fillWidth: true
                    background: Rectangle { color: Qt.darker(activePalette.window, 1.15) }
                }

                ScrollView {
                    id: docScrollView
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    ScrollBar.vertical.policy: ScrollBar.AlwaysOn
                    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                    contentWidth: availableWidth

                    ColumnLayout {
                        width: docScrollView.availableWidth
                        spacing: 4

                        // Node name heading (with search highlight when filter is active)
                        Label {
                            visible: root.selectedNodeName !== ""
                            textFormat: root.hasActiveFilter ? Text.RichText : Text.AutoText
                            text: root.hasActiveFilter
                                  ? root.highlightText(root.selectedNodeName, root.filterText)
                                  : root.selectedNodeName
                            font.bold: true
                            font.pointSize: 11
                            padding: 8
                            bottomPadding: 4
                            Layout.fillWidth: true
                            wrapMode: Text.WrapAtWordBoundaryOrAnywhere
                        }

                        // Documentation text
                        // When a filter is active, render as RichText with highlighted matches.
                        // When no filter, render as MarkdownText to preserve formatting.
                        TextEdit {
                            visible: root.selectedNodeName !== ""
                            padding: 8
                            topPadding: 4
                            Layout.fillWidth: true
                            width: docScrollView.availableWidth
                            textFormat: root.hasActiveFilter ? TextEdit.RichText : TextEdit.MarkdownText
                            selectByMouse: true
                            selectionColor: activePalette.highlight
                            color: activePalette.text
                            readOnly: true
                            wrapMode: TextEdit.Wrap

                            text: {
                                if (!root.selectedNodeName || !root.nodeTypesModel)
                                    return ""
                                var info = root.nodeTypesModel[root.selectedNodeName]
                                var rawText = info ? (info["documentation"] || "") : ""
                                if (!root.hasActiveFilter)
                                    return rawText
                                return root.highlightText(rawText, root.filterText)
                            }
                        }

                        // Placeholder when nothing is selected
                        Label {
                            visible: root.selectedNodeName === ""
                            text: "Select a node to view its documentation."
                            wrapMode: Text.WrapAtWordBoundaryOrAnywhere
                            padding: 12
                            opacity: 0.6
                            Layout.fillWidth: true
                        }
                    }
                }
            }
        }
    }
}
