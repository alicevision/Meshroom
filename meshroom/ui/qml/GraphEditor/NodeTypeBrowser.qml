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

    /// Compute a sorted list of categories from the node types model
    function getCategories() {
        if (!nodeTypesModel)
            return []
        var cats = {}
        for (var name in nodeTypesModel) {
            var cat = nodeTypesModel[name]["category"]
            if (!cats[cat])
                cats[cat] = true
        }
        return Object.keys(cats).sort()
    }

    /// Get sorted node names for a given category
    function getNodesForCategory(category) {
        if (!nodeTypesModel)
            return []
        var nodes = []
        for (var name in nodeTypesModel) {
            if (nodeTypesModel[name]["category"] === category)
                nodes.push(name)
        }
        return nodes.sort()
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        // Left column: categories
        Rectangle {
            Layout.preferredWidth: 130
            Layout.fillHeight: true
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
                            nodeList.currentIndex = -1
                            root.selectedNodeName = ""
                        }
                    }
                }
            }
        }

        // Divider
        Rectangle {
            width: 1
            Layout.fillHeight: true
            color: Qt.darker(activePalette.window, 1.3)
        }

        // Middle column: nodes in selected category
        Rectangle {
            Layout.preferredWidth: 160
            Layout.fillHeight: true
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

        // Divider
        Rectangle {
            width: 1
            Layout.fillHeight: true
            color: Qt.darker(activePalette.window, 1.3)
        }

        // Right column: node documentation
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
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
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    ScrollBar.vertical.policy: ScrollBar.AlwaysOn
                    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

                    ColumnLayout {
                        width: parent.width
                        spacing: 4

                        // Node name heading
                        Label {
                            visible: root.selectedNodeName !== ""
                            text: root.selectedNodeName
                            font.bold: true
                            font.pointSize: 11
                            padding: 8
                            bottomPadding: 4
                            Layout.fillWidth: true
                            wrapMode: Text.WrapAtWordBoundaryOrAnywhere
                        }

                        // Documentation text
                        TextEdit {
                            visible: root.selectedNodeName !== ""
                            padding: 8
                            topPadding: 4
                            Layout.fillWidth: true
                            width: parent.width
                            textFormat: TextEdit.MarkdownText
                            selectByMouse: true
                            selectionColor: activePalette.highlight
                            color: activePalette.text
                            readOnly: true
                            wrapMode: TextEdit.Wrap

                            text: {
                                if (!root.selectedNodeName || !root.nodeTypesModel)
                                    return ""
                                var info = root.nodeTypesModel[root.selectedNodeName]
                                return info ? (info["documentation"] || "") : ""
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
