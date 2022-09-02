import QtQuick 2.9
import QtQuick.Controls 2.4
import QtQuick.Controls 1.4 as Controls1 // SplitView
import QtQuick.Layouts 1.3
import MaterialIcons 2.2
import Controls 1.0


/**
 * NodeEditor allows to visualize and edit the parameters of a Node.
 * It mainly provides an attribute editor and a log inspector.
 */
Panel {
    id: root

    property variant node
    property bool readOnly: false
    property bool isCompatibilityNode: node && node.compatibilityIssue !== undefined

    signal attributeDoubleClicked(var mouse, var attribute)
    signal upgradeRequest()

    title: "Node" + (node !== null ? " - <b>" + node.label + "</b>" : "")
    icon: MaterialLabel { text: MaterialIcons.tune }

    headerBar: RowLayout {
        Label {
            text: {
                if (node !== null && node.isSubmittedOrRunning()) {
                    // Some chunks might be submitted but they'll all run eventually
                    if (node.elapsedTime > 0) { // At least a chunk is done running
                        return "Running for: " + getTimeStr(node.elapsedTime)
                    } else {
                        return (node.chunks.count > 1) ? "First chunk running" : "Node running"
                    }
                } else if (node !== null && node.isFinishedOrRunning()) {
                    /* Either all chunks finished running or the last one is running
                        * Placed inside an "else if" instead of "else" to avoid entering the functions
                        * when there is no real use */
                    return getTimeStr(node.elapsedTime)
                } else {
                    return ""
                }
            }
            padding: 2
            font.italic: true
            visible: {
                if (node !== null) {
                    if ((node.isFinishedOrRunning() || node.isSubmittedOrRunning())) {
                        return true
                    }
                }
                return false
            }

            ToolTip.text: {
                if (node !== null && (node.isFinishedOrRunning() || (node.isSubmittedOrRunning() && node.elapsedTime > 0))) {
                    var longestChunkTime = getLongestChunkTime(node.chunks)
                    if (longestChunkTime > 0)
                        return "Longest chunk: " + getTimeStr(longestChunkTime) + " (" + node.chunks.count + " chunks)"
                    else
                        return ""
                } else {
                    return ""
                }
            }
            ToolTip.visible: ToolTip.text ? runningTimeMa.containsMouse : false
            MouseArea {
                id: runningTimeMa
                anchors.fill: parent
                hoverEnabled: true
            }

            function getTimeStr(elapsed)
            {
                if (elapsed <= 0)
                    return ""

                var hours = 0
                var min = 0
                var finalTime = ""

                if (elapsed > 3600) {
                    hours = Math.floor(elapsed / 3600)
                    elapsed = elapsed - (hours * 3600)
                    finalTime += hours + "h"
                }
                if (elapsed > 60) {
                    min = Math.floor(elapsed / 60)
                    elapsed = elapsed - (min * 60)
                    finalTime += min + "m"
                }
                if (hours == 0 && min == 0) {
                    // Millisecond precision for execution times below 1 min
                    finalTime += Number(elapsed.toLocaleString(Qt.locale('en-US'))) + "s"
                } else {
                    finalTime += Math.round(elapsed) + "s"
                }

                return finalTime
            }

            function getLongestChunkTime(chunks)
            {
                if (chunks.count <= 1)
                    return 0

                var longestChunkTime = 0
                for (var i = 0; i < chunks.count; i++) {
                    var elapsedTime = chunks.at(i).elapsedTime
                    longestChunkTime = elapsedTime > longestChunkTime ? elapsedTime : longestChunkTime
                }
                return longestChunkTime
            }
        }

        MaterialToolButton {
            text: MaterialIcons.more_vert
            font.pointSize: 11
            padding: 2
            onClicked: settingsMenu.open()
            checkable: true
            checked: settingsMenu.visible
            Menu {
                id: settingsMenu
                y: parent.height
                MenuItem {
                    id: advancedToggle
                    text: "Advanced Attributes"
                    MaterialLabel {
                        anchors.right: parent.right; anchors.rightMargin: parent.padding;
                        text: MaterialIcons.build
                        anchors.verticalCenter: parent.verticalCenter
                        font.pointSize: 8
                    }
                    checkable: true
                    checked: GraphEditorSettings.showAdvancedAttributes
                    onClicked: GraphEditorSettings.showAdvancedAttributes = !GraphEditorSettings.showAdvancedAttributes
                }
                MenuItem {
                    text: "Open Cache Folder"
                    enabled: root.node !== null
                    onClicked: Qt.openUrlExternally(Filepath.stringToUrl(root.node.internalFolder))
                }
                MenuSeparator {}
                MenuItem {
                    enabled: root.node !== null
                    text: "Clear Pending Status"
                    onClicked: node.clearSubmittedChunks()
                }
            }
        }
    }
    ColumnLayout {
        anchors.fill: parent

        // CompatibilityBadge banner for CompatibilityNode
        Loader {
            active: root.isCompatibilityNode
            Layout.fillWidth: true
            visible: active  // for layout update

            sourceComponent: CompatibilityBadge {
                canUpgrade: root.node.canUpgrade
                issueDetails: root.node.issueDetails
                onUpgradeRequest: root.upgradeRequest()
                sourceComponent: bannerDelegate
            }
        }

        Loader {
            Layout.fillHeight: true
            Layout.fillWidth: true
            sourceComponent: root.node ? editor_component : placeholder_component

            Component {
                id: placeholder_component

                Item {
                    Column {
                        anchors.centerIn: parent
                        MaterialLabel {
                            text: MaterialIcons.select_all
                            font.pointSize: 34
                            color: Qt.lighter(palette.mid, 1.2)
                            anchors.horizontalCenter: parent.horizontalCenter
                        }
                        Label {
                            color: Qt.lighter(palette.mid, 1.2)
                            text: "Select a Node to access its Details"
                        }
                    }
                }
            }

            Component {
                id: editor_component

                Controls1.SplitView {
                    anchors.fill: parent

                    // The list of chunks
                    ChunksListView {
                        id: chunksLV
                        visible: (tabBar.currentIndex >= 1 && tabBar.currentIndex <= 3)
                        chunks: root.node.chunks
                    }

                    StackLayout {
                        Layout.fillHeight: true
                        Layout.fillWidth: true

                        currentIndex: tabBar.currentIndex

                        AttributeEditor {
                            Layout.fillHeight: true
                            Layout.fillWidth: true
                            model: root.node.attributes
                            readOnly: root.readOnly || root.isCompatibilityNode
                            onAttributeDoubleClicked: root.attributeDoubleClicked(mouse, attribute)
                            onUpgradeRequest: root.upgradeRequest()
                        }

                        Loader {
                            active: (tabBar.currentIndex === 1)
                            Layout.fillHeight: true
                            Layout.fillWidth: true
                            sourceComponent: NodeLog {
                                // anchors.fill: parent
                                Layout.fillHeight: true
                                Layout.fillWidth: true
                                width: parent.width
                                height: parent.height
                                id: nodeLog
                                node: root.node
                                currentChunkIndex: chunksLV.currentIndex
                                currentChunk: chunksLV.currentChunk
                            }
                        }

                        Loader {
                            active: (tabBar.currentIndex === 2)
                            Layout.fillHeight: true
                            Layout.fillWidth: true
                            sourceComponent: NodeStatistics {
                                id: nodeStatistics

                                Layout.fillHeight: true
                                Layout.fillWidth: true
                                node: root.node
                                currentChunkIndex: chunksLV.currentIndex
                                currentChunk: chunksLV.currentChunk
                            }
                        }

                        Loader {
                            active: (tabBar.currentIndex === 3)
                            Layout.fillHeight: true
                            Layout.fillWidth: true
                            sourceComponent: NodeStatus {
                                id: nodeStatus

                                Layout.fillHeight: true
                                Layout.fillWidth: true
                                node: root.node
                                currentChunkIndex: chunksLV.currentIndex
                                currentChunk: chunksLV.currentChunk
                            }
                        }

                        NodeDocumentation {
                            id: nodeDocumentation

                            Layout.fillHeight: true
                            Layout.fillWidth: true
                            node: root.node
                        }
                    }
                }
            }
        }

        TabBar {
            id: tabBar

            Layout.fillWidth: true
            width: childrenRect.width
            position: TabBar.Footer
            currentIndex: 0
            TabButton {
                text: "Attributes"
                padding: 4
                leftPadding: 8
                rightPadding: leftPadding
            }
            TabButton {
                text: "Log"
                leftPadding: 8
                rightPadding: leftPadding
            }
            TabButton {
                text: "Statistics"
                leftPadding: 8
                rightPadding: leftPadding
            }
            TabButton {
                text: "Status"
                leftPadding: 8
                rightPadding: leftPadding
            }
            TabButton {
                text: "Documentation"
                leftPadding: 8
                rightPadding: leftPadding
            }
        }
    }
}
