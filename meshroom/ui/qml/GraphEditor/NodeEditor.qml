import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Controls 1.0
import MaterialIcons 2.2
import Utils 1.0

/**
 * NodeEditor allows to visualize and edit the parameters of a Node.
 * It mainly provides an attribute editor and a log inspector.
 */

Panel {
    id: root

    property variant node
    property string globalStatus : node !== null ? node.globalStatus : ""
    property bool readOnly: false
    property bool isCompatibilityNode: node && node.compatibilityIssue !== undefined
    property string nodeStartDateTime: ""

    signal attributeDoubleClicked(var mouse, var attribute)
    signal upgradeRequest()

    title: "Node" + (node !== null ? " - <b>" + node.label + "</b>" + (node.label !== node.defaultLabel ? " (" + node.defaultLabel + ")" : "") : "")
    icon: MaterialLabel { text: MaterialIcons.tune }

    onGlobalStatusChanged: {
        nodeStartDateTime = ""
        if (node !== null && node.isRunning()) {
            timer.start()
        }
        else {
            timer.stop()
            if (node !== null && (node.isFinishedOrRunning() || globalStatus == "ERROR")) {
                computationInfo.text = Format.sec2timeStr(node.elapsedTime)
            }
            else {
                computationInfo.text =  ""
            }
        }
    }

    function refresh() {
        /**
         * Refresh properties of the Node Editor.
         */
        // Reset tab bar's current index
        tabBar.currentIndex = 0;
    }

    headerBar: RowLayout {
        Label {
            id: computationInfo
            color: node && node.isComputable ? Colors.statusColors[node.globalStatus] : palette.text
            Timer {
                id: timer
                interval: 2500
                triggeredOnStart: true
                repeat: true
                running: node !== null && node.isRunning()
                onTriggered: {
                    if (nodeStartDateTime === "") {
                        nodeStartDateTime = new Date(node.getStartDateTime()).getTime()
                    }
                    var now = new Date().getTime()
                    parent.text = Format.sec2timeStr((now-nodeStartDateTime)/1000)
                }
            }
            padding: 2
            font.italic: true
            visible: {
                if (node !== null) {
                    if (node.isComputable && (node.isFinishedOrRunning() || node.isSubmittedOrRunning() || node.globalStatus=="ERROR")) {
                        return true
                    }
                }
                return false
            }

            ToolTip.text: {
                if (node !== null && (node.isFinishedOrRunning() || (node.isSubmittedOrRunning() && node.elapsedTime > 0))) {
                    var longestChunkTime = getLongestChunkTime(node.chunks)
                    if (longestChunkTime > 0)
                        return "Longest chunk: " + Format.sec2timeStr(longestChunkTime) + " (" + node.chunks.count + " chunks)"
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

            function getLongestChunkTime(chunks) {
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

        SearchBar {
            id: searchBar
            toggle: true  // Enable toggling the actual text field by the search button
            Layout.minimumWidth: searchBar.width
            maxWidth: 150
            enabled: tabBar.currentIndex === 0 || tabBar.currentIndex === 5
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

                Menu {
                    id: filterAttributesMenu
                    title: "Filter Attributes"
                    RowLayout {
                        CheckBox {
                            id: outputToggle
                            text: "Output"
                            checkable: true
                            checked: GraphEditorSettings.showOutputAttributes
                            onClicked: GraphEditorSettings.showOutputAttributes = !GraphEditorSettings.showOutputAttributes 
                            enabled: tabBar.currentIndex === 0
                        }
                        CheckBox {
                            id: inputToggle
                            text: "Input"
                            checkable: true
                            checked: GraphEditorSettings.showInputAttributes
                            onClicked: GraphEditorSettings.showInputAttributes = !GraphEditorSettings.showInputAttributes 
                            enabled: tabBar.currentIndex === 0
                        }
                    }

                    MenuSeparator {}

                    RowLayout {
                        CheckBox {
                            id: defaultToggle
                            text: "Default"
                            checkable: true
                            checked: GraphEditorSettings.showDefaultAttributes
                            onClicked: GraphEditorSettings.showDefaultAttributes = !GraphEditorSettings.showDefaultAttributes 
                            enabled: tabBar.currentIndex === 0
                        }
                        CheckBox {
                            id: modifiedToggle
                            text: "Modified"
                            checkable: true
                            checked: GraphEditorSettings.showModifiedAttributes
                            onClicked: GraphEditorSettings.showModifiedAttributes = !GraphEditorSettings.showModifiedAttributes 
                            enabled: tabBar.currentIndex === 0
                        }
                    }

                    MenuSeparator {}

                    RowLayout {
                        CheckBox {
                            id: linkToggle
                            text: "Link"
                            checkable: true
                            checked: GraphEditorSettings.showLinkAttributes
                            onClicked: GraphEditorSettings.showLinkAttributes = !GraphEditorSettings.showLinkAttributes 
                            enabled: tabBar.currentIndex === 0
                        }
                        CheckBox {
                            id: notLinkToggle
                            text: "Not Link"
                            checkable: true
                            checked: GraphEditorSettings.showNotLinkAttributes
                            onClicked: GraphEditorSettings.showNotLinkAttributes = !GraphEditorSettings.showNotLinkAttributes 
                            enabled: tabBar.currentIndex === 0
                        }
                    }

                    MenuSeparator {}

                    CheckBox {
                        id: advancedToggle
                        text: "Advanced"
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
                    onClicked: {
                        node.clearSubmittedChunks()
                        timer.stop()
                    }
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
            visible: active  // For layout update

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

                MSplitView {
                    anchors.fill: parent

                    // The list of chunks
                    ChunksListView {
                        id: chunksLV
                        visible: (tabBar.currentIndex >= 1 && tabBar.currentIndex <= 3)
                        chunks: root.node.chunks
                        SplitView.preferredWidth: 55
                        SplitView.minimumWidth: 20
                    }

                    StackLayout {
                        SplitView.fillWidth: true

                        currentIndex: tabBar.currentIndex

                        AttributeEditor {
                            id: inOutAttr
                            objectsHideable: true
                            Layout.fillHeight: true
                            Layout.fillWidth: true
                            model: root.node.attributes
                            readOnly: root.readOnly || root.isCompatibilityNode
                            onAttributeDoubleClicked: function(mouse, attribute) { root.attributeDoubleClicked(mouse, attribute) }
                            onUpgradeRequest: root.upgradeRequest()
                            filterText: searchBar.text
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

                        AttributeEditor {
                            id: nodeInternalAttr
                            objectsHideable: false
                            Layout.fillHeight: true
                            Layout.fillWidth: true
                            model: root.node.internalAttributes
                            readOnly: root.readOnly || root.isCompatibilityNode
                            onAttributeDoubleClicked: function(mouse, attribute) { root.attributeDoubleClicked(mouse, attribute) }
                            onUpgradeRequest: root.upgradeRequest()
                            filterText: searchBar.text
                        }
                    }
                }
            }
        }

        TabBar {
            id: tabBar
            visible: root.node !== null

            property bool isComputable: root.node !== null && root.node.isComputable

            // The indices of the tab bar which can be shown for incomputable nodes
            readonly property var nonComputableTabIndices: [0, 4, 5];

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
                visible: tabBar.isComputable
                width: !visible ? 0 : tabBar.width / tabBar.count
                text: "Log"
                leftPadding: 8
                rightPadding: leftPadding
            }
            TabButton {
                visible: tabBar.isComputable
                width: !visible ? 0 : tabBar.width / tabBar.count
                text: "Statistics"
                leftPadding: 8
                rightPadding: leftPadding
            }
            TabButton {
                visible: tabBar.isComputable
                width: !visible ? 0 : tabBar.width / tabBar.count
                text: "Status"
                leftPadding: 8
                rightPadding: leftPadding
            }
            TabButton {
                text: "Documentation"
                leftPadding: 8
                rightPadding: leftPadding
            }
            TabButton {
                text: "Notes"
                padding: 4
                leftPadding: 8
                rightPadding: leftPadding
            }

            onVisibleChanged: {
                // If we have a node selected and the node is not Computable
                // Reset the currentIndex to 0, if the current index is not allowed for an incomputable node
                if ((root.node && !root.node.isComputable) && (nonComputableTabIndices.indexOf(tabBar.currentIndex) === -1)) {
                    tabBar.currentIndex = 0;
                }
            }
        }
    }
}
