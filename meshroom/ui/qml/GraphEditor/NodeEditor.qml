import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Controls 1.0
import MaterialIcons 2.2
import Utils 1.0
import Shapes 1.0

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

    property variant nodeName: node !== null ? node.name : undefined
    property string displayNodeName: node !== null ? node.name : ""
    property string validatedNodeName: displayNodeName
    property string displayNodeType: ""

    function updateNodeNameDisplay() {
        if (_currentScene.selectedNode) {
            const nodeName = _currentScene.selectedNode.name
            root.displayNodeName = nodeName
            root.validatedNodeName = nodeName
            // Set the display node type only if it is not contained in the node name
            const nodeType = _currentScene.selectedNode.nodeType
            root.displayNodeType = nodeName.startsWith(nodeType + "_") ? "" : nodeType
        }
    }

    Connections {
        target: _currentScene
        function onSelectedNodeChanged() {
            updateNodeNameDisplay()
        }
    }

    onNodeNameChanged: {
        updateNodeNameDisplay()
    }

    signal attributeDoubleClicked(var mouse, var attribute)
    signal inAttributeClicked(var srcItem, var mouse, var inAttributes)
    signal outAttributeClicked(var srcItem, var mouse, var outAttributes)
    signal showAttributeInViewer(var attribute)
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

    // Function to validate and apply node name change
    function validateNodeNameChange(name) {
        if (root.node && name.trim() !== "") {
            const newNodeName = _currentScene.renameNode(_currentScene.selectedNode, name.trim())
            if (newNodeName === "") {
                root.displayNodeName = root.nodeName
                root.validatedNodeName = root.nodeName
            } else {
                root.displayNodeName = newNodeName
                root.validatedNodeName = newNodeName
            }
        }
    }
    function cancelNodeNameChange() {
        // HACK: Set to an empty string to force the text to be set to the previous value.
        root.displayNodeName = ""
        root.displayNodeName = root.validatedNodeName
    }

    // Add custom title component for editing
    titleComponent: Component {
        RowLayout {
            spacing: 4

            Label {
                text: root.node === null ? "NodeEditor" : "Node -"
                topPadding: 4
                bottomPadding: 4
                rightPadding: 0
            }

            TextField {
                id: nodeNameField
                visible: root.node !== null
                text: root.displayNodeName
                // For some reason the validator does not always work
                validator: RegularExpressionValidator { regularExpression: /^[0-9A-Za-z]+$/ }
                font.bold: true
                readOnly: true
                selectByMouse: false
                verticalAlignment: Text.AlignVCenter
                topPadding: 4
                bottomPadding: 4
                leftPadding: 0

                background: Rectangle {
                    color: nodeNameField.readOnly ? "transparent" : root.palette.base
                    border.color: nodeNameField.readOnly ? "transparent" : root.palette.highlight
                    border.width: 1
                    radius: 2
                }

                function refreshText() {
                    nodeNameField.text = Qt.binding(function() { return root.displayNodeName })
                }

                MouseArea {
                    anchors.fill: parent
                    enabled: nodeNameField.readOnly
                    onDoubleClicked: {
                        if (root.node && !root.node.locked) {
                            nodeNameField.readOnly = false
                            nodeNameField.selectByMouse = true
                            nodeNameField.forceActiveFocus()
                            nodeNameField.selectAll()
                        }
                    }
                }

                Keys.onReturnPressed: {
                    if (!readOnly) {
                        root.validateNodeNameChange(text)
                        nodeNameField.refreshText()
                        readOnly = true
                        selectByMouse = false
                    }
                }

                Keys.onEnterPressed: {
                    if (!readOnly) {
                        root.validateNodeNameChange(text)
                        nodeNameField.refreshText()
                        readOnly = true
                        selectByMouse = false
                    }
                }

                Keys.onEscapePressed: {
                    if (!readOnly) {
                        root.cancelNodeNameChange()
                        nodeNameField.refreshText()
                        readOnly = true
                        selectByMouse = false
                    }
                }

                onActiveFocusChanged: {
                    if (!activeFocus && !readOnly) {
                        // Focus lost without pressing Enter - discard changes
                        root.cancelNodeNameChange()
                        nodeNameField.refreshText()
                        readOnly = true
                        selectByMouse = false
                    }
                }

                Connections {
                    target: _currentScene
                    function onSelectedNodeChanged() {
                        if (!activeFocus && !readOnly) {
                            root.cancelNodeNameChange()
                            nodeNameField.refreshText()
                            nodeNameField.readOnly = true
                            nodeNameField.selectByMouse = false
                        }
                    }
                }
            }

            // Show node type if the node name does not start with "nodeType_"
            Label {
                text: "(" + root.displayNodeType + ")"
                visible: root.displayNodeType !== "" && _currentScene.selectedNode
                topPadding: 4
                bottomPadding: 4
            }
        }
    }

    headerBar: RowLayout {
        Label {
            id: computationInfo
            color: node && node.isComputableType ? Colors.statusColors[node.globalStatus] : palette.text
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
                    if (node.isComputableType && (node.isFinishedOrRunning() || node.isSubmittedOrRunning() || node.globalStatus=="ERROR")) {
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
            enabled: tabBar.currentIndex === 0 || tabBar.currentIndex === 6
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
                        enabled: root.node ?
                            root.node.chunksCreated || root.node.hasPreprocessChunk || root.node.hasPostprocessChunk 
                            : false
                        chunks: root.node ? root.node.allChunks : null
                        visible: enabled && (tabBar.currentIndex >= 1 && tabBar.currentIndex <= 3)
                        SplitView.preferredWidth: 88  // Just fit to display "postprocess"
                        SplitView.minimumWidth: 20
                    }

                    StackLayout {
                        SplitView.fillWidth: true

                        currentIndex: tabBar.currentIndex

                        // First tab
                        MSplitView {
                            orientation: Qt.Vertical

                            // Node shape editor
                            Loader {
                                id: shapeEditorLoader
                                active: _currentScene ? 
                                    (_currentScene.selectedNode ? _currentScene.selectedNode.hasDisplayableShape : false) : false
                                sourceComponent: ShapeEditor {
                                    model: root.node.attributes
                                    filterText: searchBar.text
                                }
                                SplitView.preferredHeight: active ? 200 : 0
                                SplitView.minimumHeight: active ? 100 : 0
                                SplitView.maximumHeight: active ? 400 : 0
                            }

                            // Node attribute editor
                            AttributeEditor {
                                id: inOutAttr
                                objectsHideable: true
                                Layout.fillHeight: true
                                Layout.fillWidth: true
                                SplitView.minimumHeight: 100
                                model: root.node.attributes
                                readOnly: root.readOnly || root.isCompatibilityNode
                                onAttributeDoubleClicked: function(mouse, attribute) { root.attributeDoubleClicked(mouse, attribute) }
                                onUpgradeRequest: root.upgradeRequest()
                                onShowInViewer: function (attribute) {root.showAttributeInViewer(attribute)}
                                filterText: searchBar.text

                                onInAttributeClicked: function(srcItem, mouse, inAttributes) {
                                    root.inAttributeClicked(srcItem, mouse, inAttributes)
                                }
                                onOutAttributeClicked: function(srcItem, mouse, outAttributes) {
                                    root.outAttributeClicked(srcItem, mouse, outAttributes)
                                }
                            }
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

                        Loader {
                            active: (tabBar.currentIndex === 4)
                            Layout.fillHeight: true
                            Layout.fillWidth: true
                            sourceComponent: NodeFileBrowser {
                                id: nodeFileBrowser

                                Layout.fillHeight: true
                                Layout.fillWidth: true
                                node: root.node
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

                            onInAttributeClicked: function(srcItem, mouse, inAttributes) {
                                root.inAttributeClicked(srcItem, mouse, inAttributes)
                            }

                            onOutAttributeClicked: function(srcItem, mouse, outAttributes) {
                                root.outAttributeClicked(srcItem, mouse, outAttributes)
                            }
                        }
                    }
                }
            }
        }

        TabBar {
            id: tabBar
            visible: root.node !== null

            property bool isComputableType: root.node !== null && root.node.isComputableType
            property bool isBackdropNode: root.node !== null && root.node.isBackdropNode

            // The indices of the tab bar which can be shown for incomputable nodes
            readonly property var nonComputableTabIndices: [0, 5, 6]

            Layout.fillWidth: true
            width: childrenRect.width
            position: TabBar.Footer
            currentIndex: 0
            TabButton {
                text: "Attributes"
                visible: !tabBar.isBackdropNode
                width: {
                    if (!visible)
                        return 0
                    else {
                        if (tabBar.isComputableType)
                            return tabBar.width / tabBar.count
                        else {
                            return tabBar.width / tabBar.nonComputableTabIndices.length
                        }
                    }
                }
                padding: 4
                leftPadding: 8
                rightPadding: leftPadding
            }
            TabButton {
                visible: tabBar.isComputableType
                width: !visible ? 0 : tabBar.width / tabBar.count
                text: "Log"
                leftPadding: 8
                rightPadding: leftPadding
            }
            TabButton {
                visible: tabBar.isComputableType
                width: !visible ? 0 : tabBar.width / tabBar.count
                text: "Statistics"
                leftPadding: 8
                rightPadding: leftPadding
            }
            TabButton {
                visible: tabBar.isComputableType
                width: !visible ? 0 : tabBar.width / tabBar.count
                text: "Status"
                leftPadding: 8
                rightPadding: leftPadding
            }
            TabButton {
                visible: tabBar.isComputableType
                width: !visible ? 0 : tabBar.width / tabBar.count
                text: "Files"
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
                if ((root.node && !root.node.isComputableType) && (nonComputableTabIndices.indexOf(tabBar.currentIndex) === -1)) {
                    if (root.node.isBackdropNode) {
                        // Backdrop nodes can only show the Documentation & Notes tabs
                        tabBar.currentIndex = 5 // Documentation tab
                    } else {
                        tabBar.currentIndex = 0
                    }
                }
            }
        }
    }
}
