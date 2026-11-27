import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import MaterialIcons 2.2

/**
 * Pipeline templates of the homepage, grouped by category.
 * Categories are packed in rows of columns so that many pipelines use the width instead of the height:
 * a category shows a few rows at most, with "Show remaining" to show only this category with all its pipelines.
 */

Rectangle {
    id: root

    // [{"name", "color", "templates": [{"label", "path", "icon", "description", ...}]}]
    property var categories: []
    // Path of the template being loaded ("" for an empty project), undefined when nothing is loading
    property var loadingPath: undefined

    // Emitted with the path of the selected template
    signal pipelineSelected(string path)

    readonly property int pipelineCount: categories.reduce((count, category) => count + category.templates.length, 0)
    readonly property bool isLoading: loadingPath !== undefined

    // Lower-case name of the category shown alone with "Show remaining" (empty list: all the categories)
    property var expandedCategories: []
    readonly property int columnSpacing: 20
    readonly property int columns: Math.max(1, Math.floor((content.width + columnSpacing) / (210 + columnSpacing)))
    readonly property real columnWidth: (content.width - (columns - 1) * columnSpacing) / columns
    readonly property var categoryRows: MeshroomApp.layoutPipelineCategories(categories, columns, expandedCategories)

    function blockWidth(span) {
        return span * columnWidth + (span - 1) * columnSpacing
    }

    // Show only the category `key` with all its pipelines, or all the categories again
    function toggleCategory(key) {
        expandedCategories = expandedCategories.indexOf(key) < 0 ? [key] : []
    }

    // Small text button of the list: "Show remaining" / "Show less"
    component LinkButton: ItemDelegate {
        id: linkButton
        property string iconText: ""
        implicitHeight: 26
        leftPadding: 8
        rightPadding: 6
        topPadding: 0
        bottomPadding: 0
        hoverEnabled: true
        contentItem: RowLayout {
            spacing: 2
            opacity: linkButton.hovered ? 1.0 : 0.7
            Label {
                text: linkButton.text
                font.pixelSize: 12
            }
            Label {
                font.family: MaterialIcons.fontFamily
                text: linkButton.iconText
                font.pixelSize: 16
            }
        }
        background: Rectangle {
            radius: 4
            color: linkButton.hovered ? palette.button : "transparent"
        }
    }

    // One pipeline template: icon in the category color and label, description as tooltip
    component PipelineButton: ItemDelegate {
        id: pipelineDelegate
        property var template
        property color categoryColor
        implicitHeight: 30
        leftPadding: 8
        rightPadding: 8
        topPadding: 0
        bottomPadding: 0
        hoverEnabled: true
        enabled: !root.isLoading || root.loadingPath === template.path
        opacity: enabled ? 1.0 : 0.4

        ToolTip.visible: hovered && template.description
        ToolTip.text: template.description
        ToolTip.delay: 500

        contentItem: RowLayout {
            spacing: 8
            Label {
                font.family: MaterialIcons.fontFamily
                text: MaterialIcons[pipelineDelegate.template.icon] || MaterialIcons.account_tree
                font.pixelSize: 15
                color: pipelineDelegate.categoryColor
            }
            Label {
                Layout.fillWidth: true
                text: pipelineDelegate.template.label
                font.pixelSize: 13
                elide: Text.ElideRight
            }
            BusyIndicator {
                Layout.preferredWidth: 18
                Layout.preferredHeight: 18
                running: root.loadingPath === pipelineDelegate.template.path
                visible: running
            }
        }

        background: Rectangle {
            radius: 4
            color: pipelineDelegate.hovered ? palette.button : "transparent"
            border.color: pipelineDelegate.hovered ? palette.mid : "transparent"
        }

        onClicked: root.pipelineSelected(template.path)
    }

    implicitHeight: content.implicitHeight + 20
    radius: 6
    color: Qt.darker(palette.window, 1.1)
    border.color: palette.mid

    Item {
        id: content
        anchors.fill: parent
        anchors.leftMargin: 12
        anchors.rightMargin: 12
        anchors.topMargin: 10
        anchors.bottomMargin: 10
        implicitHeight: root.pipelineCount > 0 ? rowsColumn.implicitHeight : emptyLabel.implicitHeight

        Label {
            id: emptyLabel
            visible: root.pipelineCount === 0
            width: parent.width
            text: "No pipeline available: install plugins providing pipelines from the Plugin Manager."
            font.pixelSize: 13
            opacity: 0.6
        }

        // Categories packed in rows of columns of at least 210 px (see templateInfo.layoutCategories)
        Column {
            id: rowsColumn
            visible: root.pipelineCount > 0
            width: parent.width
            spacing: 8

            Repeater {
                model: root.categoryRows

                delegate: Row {
                    spacing: root.columnSpacing

                    Repeater {
                        model: modelData

                        delegate: Column {
                            id: categoryBlock
                            width: root.blockWidth(block.span)
                            spacing: 1

                            property var block: modelData
                            property string categoryKey: block.name.toLowerCase()

                            // Category header: a colored bar, the category name and its pipeline count
                            RowLayout {
                                width: parent.width
                                height: 26
                                spacing: 7
                                Rectangle {
                                    Layout.leftMargin: 8
                                    implicitWidth: 3
                                    implicitHeight: 11
                                    radius: 1
                                    color: categoryBlock.block.color
                                }
                                Label {
                                    text: (categoryBlock.block.name || "Other").toUpperCase()
                                    font.pixelSize: 11
                                    font.weight: Font.DemiBold
                                    font.letterSpacing: 0.7
                                    opacity: 0.6
                                }
                                Label {
                                    text: categoryBlock.block.count
                                    font.pixelSize: 11
                                    opacity: 0.6
                                }
                                Item { Layout.fillWidth: true }
                                LinkButton {
                                    visible: categoryBlock.block.expanded
                                    text: "Show less"
                                    iconText: MaterialIcons.expand_less
                                    onClicked: root.toggleCategory(categoryBlock.categoryKey)
                                }
                            }

                            // Pipelines from top to bottom, then left to right
                            Grid {
                                columns: categoryBlock.block.span
                                rows: categoryBlock.block.rows
                                flow: Grid.TopToBottom
                                columnSpacing: root.columnSpacing
                                rowSpacing: 1

                                Repeater {
                                    model: categoryBlock.block.templates

                                    delegate: PipelineButton {
                                        width: root.columnWidth
                                        template: modelData
                                        categoryColor: categoryBlock.block.color
                                    }
                                }
                                // Last cell of a category with more pipelines than shown
                                LinkButton {
                                    visible: categoryBlock.block.truncated
                                    height: 30
                                    text: "Show remaining " + categoryBlock.block.remaining
                                    iconText: MaterialIcons.expand_more
                                    onClicked: root.toggleCategory(categoryBlock.categoryKey)
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
