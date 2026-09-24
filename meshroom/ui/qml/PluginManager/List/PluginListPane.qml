import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Controls 1.0
import MaterialIcons 2.2

import "../Common/PluginUtils.js" as PluginUtils

/**
 * PluginListPane displays plugins as a sortable table (name/version/type/publisher/path) and exposes
 * the current selection through `currentPlugin`.
 */

Panel {
    id: root

    // Bumped after a registry refresh to re-run the search.
    property int refreshRevision: 0
    readonly property var plugins: {
        root.refreshRevision
        return _pluginManager.searchPlugin([root.searchText], false, root.showInstalled, root.showNotInstalled)
    }
    readonly property var currentPlugin: listView.currentItem ? listView.currentItem.pluginData : null

    property int rowSpacing: 8
    property int rowPadding: 14

    // All columns are proportional to the available width.
    property real versionColumnRatio: 0.12
    property real typeColumnRatio: 0.12
    property real publisherColumnRatio: 0.18
    property real urlColumnRatio: 0.35

    // Compute columns width.
    // Padding + 4 spacing gaps.
    readonly property int availableColumnsWidth: Math.max(0, root.width - 2 * root.rowPadding - 4 * root.rowSpacing)
    readonly property int versionColumnWidth: Math.round(root.availableColumnsWidth * root.versionColumnRatio)
    readonly property int typeColumnWidth: Math.round(root.availableColumnsWidth * root.typeColumnRatio)
    readonly property int publisherColumnWidth: Math.round(root.availableColumnsWidth * root.publisherColumnRatio)
    readonly property int urlColumnWidth: Math.round(root.availableColumnsWidth * root.urlColumnRatio)
    readonly property int nameColumnWidth: Math.max(0, root.availableColumnsWidth - root.versionColumnWidth
                                                         - root.typeColumnWidth - root.publisherColumnWidth
                                                         - root.urlColumnWidth)

    // Filter / Sort states.
    property string sortColumn: "type"
    property bool sortAscending: true
    property string searchText: ""
    property bool showInstalled: true
    property bool showNotInstalled: true

    title: "Plugin List"
    background: Rectangle { color: palette.base }

    // Refreshes the plugin registries and update the list.
    function refresh(useTTL) {
        _pluginManager.refreshPluginRegistries(true, useTTL)
        root.refreshRevision++
    }

    // "url" (the Path column) and "type" need deriving.
    function columnValue(item, column) {
        if (column === "url")
            return PluginUtils.pluginPath(item)
        if (column === "type")
            return item.typeName || ""
        return item[column]
    }

    // Toggles sort direction when the same column is clicked again, otherwise switches column.
    function sortBy(column) {
        if (root.sortColumn === column) {
            root.sortAscending = !root.sortAscending
        } else {
            root.sortColumn = column
            root.sortAscending = true
        }
    }

    // Refresh the plugin registries when the pane is created.
    Component.onCompleted: {
        if (_pluginManager.localPluginsEnabled)
            root.refresh(true)
    }

    // Sorted plugins.
    // Re-evaluated whenever sortColumn/sortAscending/plugins change.
    property var sortedPlugins: {
        var arr = root.plugins.slice()
        arr.sort(function(a, b) {
            var va = root.columnValue(a, root.sortColumn)
            var vb = root.columnValue(b, root.sortColumn)
            if (typeof va === "boolean") {
                va = va ? 1 : 0
                vb = vb ? 1 : 0
            } else {
                va = String(va).toLowerCase()
                vb = String(vb).toLowerCase()
                // Empty values always go last, whatever the sort direction
                if (va === "" || vb === "")
                    return va === vb ? 0 : (va === "" ? 1 : -1)
            }
            var result = va < vb ? -1 : (va > vb ? 1 : 0)
            return root.sortAscending ? result : -result
        })
        return arr
    }

    // Layout
    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // Toolbar
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: toolbarRow.implicitHeight + 12
            color: palette.window

            RowLayout {
                id: toolbarRow
                anchors.fill: parent
                anchors.leftMargin: root.rowPadding
                anchors.rightMargin: root.rowPadding
                anchors.topMargin: 6
                anchors.bottomMargin: 6
                spacing: root.rowSpacing

                // Search Icon
                Label {
                    text: MaterialIcons.search
                    font.family: MaterialIcons.fontFamily
                    font.pointSize: 12
                    color: palette.text
                }

                // Search Field
                TextField {
                    placeholderText: "Search plugins..."
                    placeholderTextColor: palette.mid
                    Layout.fillWidth: true
                    text: root.searchText
                    onTextChanged: root.searchText = text
                }

                // Filter Installed
                CheckBox {
                    text: "Installed"
                    checked: root.showInstalled
                    onToggled: root.showInstalled = checked
                    enabled: _pluginManager.localPluginsEnabled
                }

                // Filter Available
                CheckBox {
                    text: "Available"
                    checked: _pluginManager.localPluginsEnabled ? root.showNotInstalled : false
                    onToggled: root.showNotInstalled = checked
                    enabled: _pluginManager.localPluginsEnabled
                }

                // Refresh Records
                MaterialToolButton {
                    text: MaterialIcons.sync
                    ToolTip.text: "Refresh List"
                    ToolTip.visible: hovered
                    enabled: _pluginManager.localPluginsEnabled
                    onClicked: root.refresh(false) // useTTL=false
                }
            }
        }

        // Column Headers
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: headerRow.implicitHeight + 8
            color: Qt.darker(palette.base, 1.15)

            RowLayout {
                id: headerRow
                anchors.fill: parent
                anchors.leftMargin: root.rowPadding
                anchors.rightMargin: root.rowPadding
                anchors.topMargin: 4
                anchors.bottomMargin: 4
                spacing: root.rowSpacing

                // Name Column
                PluginColumnHeader {
                    label: "Name"
                    column: "name"
                    sortColumn: root.sortColumn
                    sortAscending: root.sortAscending
                    Layout.preferredWidth: root.nameColumnWidth
                    onClicked: root.sortBy("name")
                }

                // Version Column
                PluginColumnHeader {
                    label: "Version"
                    column: "version"
                    sortColumn: root.sortColumn
                    sortAscending: root.sortAscending
                    Layout.preferredWidth: root.versionColumnWidth
                    onClicked: root.sortBy("version")
                }

                // Type Column
                PluginColumnHeader {
                    label: "Type"
                    column: "type"
                    sortColumn: root.sortColumn
                    sortAscending: root.sortAscending
                    Layout.preferredWidth: root.typeColumnWidth
                    onClicked: root.sortBy("type")
                }

                // Publisher Column
                PluginColumnHeader {
                    label: "Publisher"
                    column: "publisher"
                    sortColumn: root.sortColumn
                    sortAscending: root.sortAscending
                    Layout.preferredWidth: root.publisherColumnWidth
                    onClicked: root.sortBy("publisher")
                }

                // Path / URL Column
                PluginColumnHeader {
                    label: "Path / URL"
                    column: "url"
                    sortColumn: root.sortColumn
                    sortAscending: root.sortAscending
                    Layout.preferredWidth: root.urlColumnWidth
                    onClicked: root.sortBy("url")
                }
            }
        }

        // Separator
        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: palette.mid
        }

        // List View
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: palette.base

            ListView {
                id: listView
                anchors.fill: parent
                clip: true
                model: root.sortedPlugins
                currentIndex: 0

                delegate: PluginListItemDelegate {
                    pluginData: modelData
                    nameColumnWidth: root.nameColumnWidth
                    versionColumnWidth: root.versionColumnWidth
                    typeColumnWidth: root.typeColumnWidth
                    publisherColumnWidth: root.publisherColumnWidth
                    urlColumnWidth: root.urlColumnWidth
                    rowSpacing: root.rowSpacing
                    rowPadding: root.rowPadding
                    onClicked: listView.currentIndex = index
                }
            }

            // Placeholder
            Label {
                anchors.centerIn: parent
                visible: listView.count === 0
                text: "No plugins"
                opacity: 0.6
            }
        }
    }
}
