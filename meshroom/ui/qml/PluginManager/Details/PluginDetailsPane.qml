import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Controls 1.0
import MaterialIcons 2.2

import "../Common"
import "../Common/PluginUtils.js" as PluginUtils

/**
 * PluginDetailsPane shows the full description of a single plugin.
 */

Panel {
    id: root

    property var plugin: null
    property bool actionsEnabled: true  // Whether the install / update / remove buttons can be used.
    readonly property bool isExternalPlugin: !!plugin && ["REZ", "PATH", "BUILTIN"].indexOf(plugin.typeName) !== -1
    readonly property var updateRecord: root.plugin ? _pluginManager.getUpdateRecord(root.plugin) : null

    // Signals
    signal installRequested()
    signal updateRequested()
    signal removeRequested()

    title: "Plugin Details"
    background: Rectangle { color:palette.window }

    // Placeholder
    Column {
        anchors.centerIn: parent
        spacing: 8
        visible: root.plugin === null

        MaterialLabel {
            text: MaterialIcons.extension
            font.pointSize: 28
            color: Qt.lighter(palette.mid, 1.2)
            anchors.horizontalCenter: parent.horizontalCenter
        }

        Label {
            text: "Select a Plugin to access its Details"
            color: Qt.lighter(palette.mid, 1.2)
        }
    }

    // Layout
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 6
        visible: root.plugin !== null

        // Plugin Name + Type Badge
        RowLayout {
            Layout.fillWidth: true
            spacing: 6

            Label {
                text: root.plugin ? root.plugin.name : ""
                font.bold: true
                font.pointSize: 12
                Layout.fillWidth: true
                elide: Text.ElideRight
            }

            PluginTypeBadge {
                Layout.alignment: Qt.AlignTop
                visible: root.plugin !== null
                typeName: root.plugin ? (root.plugin.typeName || "") : ""
            }
        }

        // Plugin Version
        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            visible: !!(root.plugin && root.plugin.version)

            Label {
                text: root.plugin ? "Version " + root.plugin.version : ""
            }

            Label {
                text: MaterialIcons.update
                font.family: MaterialIcons.fontFamily
                color: "goldenrod"
                visible: root.updateRecord !== null
            }

            Label {
                text: root.updateRecord ? root.updateRecord.version + " available" : ""
                visible: root.updateRecord !== null
                color: "goldenrod"
                elide: Text.ElideRight
            }
        }

        // Plugin Publisher
        RowLayout {
            Layout.fillWidth: true
            spacing: 0
            visible: !!(root.plugin && root.plugin.publisher)

            Label {
                text: "Published by "
                elide: Text.ElideRight
            }

            PluginPublisherLabel {
                plugin: root.plugin
            }
        }

        // Plugin Link
        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            visible: !!(root.plugin && PluginUtils.pluginPath(root.plugin) && !PluginUtils.isInstalled(root.plugin))

            HoverHandler { cursorShape: Qt.PointingHandCursor }
            TapHandler { onTapped: Qt.openUrlExternally(PluginUtils.pluginPath(root.plugin)) }

            Label {
                text: MaterialIcons.link
                font.family: MaterialIcons.fontFamily
                color: palette.link
            }

            Label {
                text: root.plugin ? PluginUtils.pluginPath(root.plugin) : ""
                color: palette.link
                Layout.fillWidth: true
                elide: Text.ElideRight
            }
        }

        // Separator
        Rectangle {
            Layout.fillWidth: true
            Layout.topMargin: 5
            height: 1
            color: palette.mid
            visible: root.plugin !== null
        }

        // Plugin Description + Authors + Requirements
        ScrollView {
            id: detailsScroll
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

            ColumnLayout {
                width: detailsScroll.availableWidth
                spacing: 20

                // Spacer
                Item { Layout.fillWidth: true }

                // Plugin Description
                Label {
                    text: root.plugin ? (root.plugin.description || "") : ""
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                    visible: !!(root.plugin && root.plugin.description)
                }

                // Plugin Authors
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 6
                    visible: !!(root.plugin && root.plugin.authors && root.plugin.authors.length > 0)

                    Label {
                        text: "Author(s):"
                        Layout.fillWidth: true
                        color: Qt.darker(palette.text, 1.175)
                        bottomPadding: 4
                    }

                    Repeater {
                        model: root.plugin && root.plugin.authors ? root.plugin.authors : []

                        delegate: RowLayout {
                            Layout.fillWidth: true
                            spacing: 6

                            Label {
                                text: MaterialIcons.person
                                font.family: MaterialIcons.fontFamily
                                Layout.alignment: Qt.AlignTop
                            }

                            Label {
                                text: modelData
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }
                        }
                    }
                }

                // Plugin Requirements
                NoticePane {
                    title: "Requirements"
                    text: root.plugin ? (root.plugin.requirements || "") : ""
                    Layout.fillWidth: true
                    visible: !!(root.plugin && root.plugin.requirements)
                }

                // Spacer
                Item { Layout.fillWidth: true }
            }
        }

        // Separator
        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: palette.mid
            visible: root.plugin !== null && !root.isExternalPlugin
        }

        // Bottom Controls
        Item {
            Layout.fillWidth: true
            implicitHeight: buttonsRow.implicitHeight + 16
            visible: root.plugin !== null && !root.isExternalPlugin

            // Buttons Row
            RowLayout {
                id: buttonsRow
                anchors.fill: parent
                anchors.margins: 8

                // Float Right
                Item {
                    Layout.fillWidth: true
                }

                Button {
                    text: "Install"
                    enabled: root.actionsEnabled
                    palette.button: "darkgreen"
                    palette.buttonText: "white"
                    visible: root.plugin !== null && !root.isExternalPlugin && !PluginUtils.isInstalled(root.plugin)
                    onClicked: root.installRequested()
                }

                Button {
                    text: "Update"
                    enabled: root.actionsEnabled
                    palette.button: "darkgoldenrod"
                    palette.buttonText: "white"
                    visible: root.plugin !== null && !root.isExternalPlugin && PluginUtils.isInstalled(root.plugin) && root.updateRecord !== null
                    onClicked: root.updateRequested()
                }

                Button {
                    text: "Remove"
                    enabled: root.actionsEnabled
                    palette.button: "darkred"
                    palette.buttonText: "white"
                    visible: root.plugin !== null && !root.isExternalPlugin && PluginUtils.isInstalled(root.plugin)
                    onClicked: root.removeRequested()
                }
            }
        }
    }
}
