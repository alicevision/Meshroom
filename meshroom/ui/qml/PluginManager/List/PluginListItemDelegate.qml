import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import MaterialIcons 2.2

import "../Common"
import "../Common/PluginUtils.js" as PluginUtils

/**
 * PluginListItemDelegate renders one row of the plugins table: name / version / type / publisher / path.
 * Column widths are exposed as properties so they can be kept in sync with the table header.
 */

ItemDelegate {
    id: root

    property var pluginData: modelData
    // The PluginRecord describing an available update for "pluginData", or null.
    readonly property var updateRecord: PluginUtils.isInstalled(root.pluginData) ? _pluginManager.getUpdateRecord(root.pluginData) : null
    property int nameColumnWidth: 200
    property int versionColumnWidth: 60
    property int typeColumnWidth: 90
    property int publisherColumnWidth: 140
    property int urlColumnWidth: 140
    property int rowSpacing: 8
    property int rowPadding: 8

    width: ListView.view ? ListView.view.width : implicitWidth
    highlighted: ListView.isCurrentItem
    hoverEnabled: true
    leftPadding: root.rowPadding
    rightPadding: root.rowPadding
    topPadding: root.rowPadding
    bottomPadding: root.rowPadding

    HoverHandler { cursorShape: Qt.PointingHandCursor }

    background: Rectangle {
        color: root.highlighted ? palette.window
               : root.hovered ? Qt.lighter(palette.base, 1.150)
               : palette.base

        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: 1
            color: palette.mid
        }
    }

    contentItem: RowLayout {
        spacing: root.rowSpacing

        // Name
        Label {
            text: root.pluginData.name || "Unknown"
            font.bold: true
            Layout.preferredWidth: root.nameColumnWidth
            elide: Text.ElideRight
        }

        // Version
        RowLayout {
            Layout.preferredWidth: root.versionColumnWidth
            spacing: 4

            // Version Label
            Label {
                text: root.pluginData.version || "Unknown"
                elide: Text.ElideRight
                color: root.updateRecord !== null ? "goldenrod" : palette.windowText
            }

            // Update Icon
            Label {
                text: MaterialIcons.update
                font.family: MaterialIcons.fontFamily
                font.pointSize: 12
                color: "goldenrod"
                visible: root.updateRecord !== null
                ToolTip.visible: updateIconHover.hovered
                ToolTip.text: root.updateRecord ? "Update to " + root.updateRecord.version + " available" : ""

                HoverHandler { id: updateIconHover }
            }

            // Float Left
            Item { Layout.fillWidth: true }
        }

        // Type
        Item {
            Layout.preferredWidth: root.typeColumnWidth
            Layout.fillHeight: true

            PluginTypeBadge {
                anchors.verticalCenter: parent.verticalCenter
                typeName: root.pluginData.typeName || ""
                visible: root.pluginData
            }
        }

        // Publisher
        Item {
            Layout.preferredWidth: root.publisherColumnWidth
            Layout.fillHeight: true

            PluginPublisherLabel {
                anchors.verticalCenter: parent.verticalCenter
                plugin: root.pluginData
            }
        }

        // Path / Url
        RowLayout {
            Layout.preferredWidth: root.urlColumnWidth
            spacing: 2

            // Path / Url Label
            Label {
                text: PluginUtils.pluginPath(root.pluginData) || ""
                elide: Text.ElideRight
                Layout.fillWidth: true
            }

            // Clipboard Button
            MaterialToolButton {
                text: MaterialIcons.copy_all
                font.pointSize: 10
                ToolTip.text: "Copy Path / Url to clipboard"
                visible: !!PluginUtils.pluginPath(root.pluginData)

                HoverHandler {
                    cursorShape: Qt.PointingHandCursor
                }

                onClicked: {
                    Clipboard.clear()
                    Clipboard.setText(PluginUtils.pluginPath(root.pluginData))
                }
            }
        }
    }
}
