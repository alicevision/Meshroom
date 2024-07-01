import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls 1.4 as Controls1 // For SplitView
import QtQuick.Layouts 1.11
import QtQuick.Window 2.15
import QtQml.Models 2.15

import Qt.labs.platform 1.0 as Platform
import QtQuick.Dialogs 1.3

import Qt.labs.settings 1.0
import GraphEditor 1.0
import MaterialIcons 2.2
import Utils 1.0
import Controls 1.0

Page {
    id: root
    Settings {
        id: settings_UILayout
        category: 'UILayout'
        property alias showLiveReconstruction: liveSfMVisibilityCB.checked
        property alias showGraphEditor: graphEditorVisibilityCB.checked
        property alias showImageViewer: imageViewerVisibilityCB.checked
        property alias showViewer3D: viewer3DVisibilityCB.checked
    }

    // Utility functions for elements in the menubar

    function initFileDialogFolder(dialog, importImages = false) {
        let folder = "";

        if (imagesFolder.toString() === "" && workspaceView.imageGallery.galleryGrid.itemAtIndex(0) !== null) {
            imagesFolder = Filepath.stringToUrl(Filepath.dirname(workspaceView.imageGallery.galleryGrid.itemAtIndex(0).source))
        }

        if (_reconstruction.graph && _reconstruction.graph.filepath) {
            folder = Filepath.stringToUrl(Filepath.dirname(_reconstruction.graph.filepath))
        } else {
            var projects = MeshroomApp.recentProjectFiles;
            if (projects.length > 0 && Filepath.exists(projects[0])) {
                folder = Filepath.stringToUrl(Filepath.dirname(projects[0]))
            }
        }

        if (importImages && imagesFolder.toString() !== "" && Filepath.exists(imagesFolder)) {
            folder = imagesFolder
        }

        dialog.folder = folder
    }

    Action {
        id: loadTemplateAction

        property string tooltip: "Load a template like a regular project file (any \"Publish\" node will be displayed)"
        text: "Load Template"
        onTriggered: {
            ensureSaved(function() {
                initFileDialogFolder(loadTemplateDialog);
                loadTemplateDialog.open();
            })
        }
    }

    header: RowLayout {
        spacing: 0
        MaterialToolButton {
            id: homeButton
            text: MaterialIcons.home

            font.pointSize: 18

            background: Rectangle {
                color: homeButton.hovered ? activePalette.highlight : Qt.darker(activePalette.window, 1.15)
                border.color: Qt.darker(activePalette.window, 1.15)
            }

            onClicked: ensureSaved(function() {
                _reconstruction.clear()
                if (mainStack.depth == 1)
                    mainStack.replace("Homepage.qml")
                else
                    mainStack.pop()
            })
        }
        MenuBar {
            palette.window: Qt.darker(activePalette.window, 1.15)
            Menu {
                title: "File"
                Menu {
                    id: newPipelineMenu
                    title: "New Pipeline"
                    enabled: newPipelineMenuItems.model !== undefined && newPipelineMenuItems.model.length > 0
                    property int maxWidth: 1000
                    property int fullWidth: {
                        var result = 0;
                        for (var i = 0; i < count; ++i) {
                            var item = itemAt(i)
                            result = Math.max(item.implicitWidth + item.padding * 2, result)
                        }
                        return result;
                    }
                    implicitWidth: fullWidth
                    Repeater {
                        id: newPipelineMenuItems
                        model: MeshroomApp.pipelineTemplateFiles
                        MenuItem {
                            onTriggered: ensureSaved(function() {
                                _reconstruction.new(modelData["key"])
                            })

                            text: fileTextMetrics.elidedText
                            TextMetrics {
                                id: fileTextMetrics
                                text: modelData["name"]
                                elide: Text.ElideLeft
                                elideWidth: newPipelineMenu.maxWidth
                            }
                            ToolTip.text: modelData["path"]
                            ToolTip.visible: hovered
                            ToolTip.delay: 200
                        }
                    }
                }
                Action {
                    id: openActionItem
                    text: "Open"
                    shortcut: "Ctrl+O"
                    onTriggered: ensureSaved(function() {
                            initFileDialogFolder(openFileDialog)
                            openFileDialog.open()
                        })
                }
                Menu {
                    id: openRecentMenu
                    title: "Open Recent"
                    enabled: recentFilesMenuItems.model !== undefined && recentFilesMenuItems.model.length > 0
                    property int maxWidth: 1000
                    property int fullWidth: {
                        var result = 0;
                        for (var i = 0; i < count; ++i) {
                            var item = itemAt(i)
                            result = Math.max(item.implicitWidth + item.padding * 2, result)
                        }
                        return result
                    }
                    implicitWidth: fullWidth
                    Repeater {
                        id: recentFilesMenuItems
                        model: MeshroomApp.recentProjectFiles
                        MenuItem {
                            onTriggered: ensureSaved(function() {
                                openRecentMenu.dismiss()
                                if (_reconstruction.loadUrl(modelData["path"])) {
                                    MeshroomApp.addRecentProjectFile(modelData["path"])
                                } else {
                                    MeshroomApp.removeRecentProjectFile(modelData["path"])
                                }
                            })
                            
                            text: fileTextMetrics.elidedText
                            TextMetrics {
                                id: fileTextMetrics
                                text: modelData["path"]
                                elide: Text.ElideLeft
                                elideWidth: openRecentMenu.maxWidth
                            }
                        }
                    }
                }
                MenuSeparator { }
                Action {
                    id: saveAction
                    text: "Save"
                    shortcut: "Ctrl+S"
                    enabled: _reconstruction ? (_reconstruction.graph && !_reconstruction.graph.filepath) || !_reconstruction.undoStack.clean : false
                    onTriggered: {
                        if (_reconstruction.graph.filepath) {
                            // get current time date
                            var date = _reconstruction.graph.getFileDateVersionFromPath(_reconstruction.graph.filepath)

                            // check if the file has been modified by another instance
                            if (_reconstruction.graph.fileDateVersion !== date) {
                                fileModifiedDialog.open()
                            } else
                                _reconstruction.save()
                        } else {
                            initFileDialogFolder(saveFileDialog)
                            saveFileDialog.open()
                        }
                    }
                }
                Action {
                    id: saveAsAction
                    text: "Save As..."
                    shortcut: "Ctrl+Shift+S"
                    onTriggered: {
                        initFileDialogFolder(saveFileDialog)
                        saveFileDialog.open()
                    }
                }
                MenuSeparator { }
                Action {
                    id: importImagesAction
                    text: "Import Images"
                    shortcut: "Ctrl+I"
                    onTriggered: {
                        initFileDialogFolder(importImagesDialog, true)
                        importImagesDialog.open()
                    }
                }

                MenuItem {
                    action: removeAllImagesAction
                    ToolTip.visible: hovered
                    ToolTip.text: removeAllImagesAction.tooltip
                }

                MenuSeparator { }
                Menu {
                    id: advancedMenu
                    title: "Advanced"
                    implicitWidth: 300

                    Action {
                        id: saveAsTemplateAction
                        text: "Save As Template..."
                        shortcut: Shortcut {
                            sequence: "Ctrl+Shift+T"
                            context: Qt.ApplicationShortcut
                            onActivated: saveAsTemplateAction.triggered()
                        }
                        onTriggered: {
                            initFileDialogFolder(saveTemplateDialog)
                            saveTemplateDialog.open()
                        }
                    }

                    MenuItem {
                        action: loadTemplateAction
                        ToolTip.visible: hovered
                        ToolTip.text: loadTemplateAction.tooltip
                    }

                    Action {
                        id: importProjectAction
                        text: "Import Project"
                        shortcut: Shortcut {
                            sequence: "Ctrl+Shift+I"
                            context: Qt.ApplicationShortcut
                            onActivated: importProjectAction.triggered()
                        }
                        onTriggered: {
                            initFileDialogFolder(importProjectDialog)
                            importProjectDialog.open()
                        }
                    }

                    MenuItem {
                        action: removeImagesFromAllGroupsAction
                        ToolTip.visible: hovered
                        ToolTip.text: removeImagesFromAllGroupsAction.tooltip
                    }
                }
                MenuSeparator { }
                Action {
                    text: "Quit"
                    onTriggered: _window.close()
                }
            }
            Menu {
                title: "Edit"
                MenuItem {
                    action: undoAction
                    ToolTip.visible: hovered
                    ToolTip.text: undoAction.tooltip
                }
                MenuItem {
                    action: redoAction
                    ToolTip.visible: hovered
                    ToolTip.text: redoAction.tooltip
                }
                MenuItem {
                    action: cutAction
                    ToolTip.visible: hovered
                    ToolTip.text: cutAction.tooltip
                }
                MenuItem {
                    action: copyAction
                    ToolTip.visible: hovered
                    ToolTip.text: copyAction.tooltip
                }
                MenuItem {
                    action: pasteAction
                    ToolTip.visible: hovered
                    ToolTip.text: pasteAction.tooltip
                }
            }
            Menu {
                title: "View"
                MenuItem {
                    id: graphEditorVisibilityCB
                    text: "Graph Editor"
                    checkable: true
                    checked: true
                }
                MenuItem {
                    id: liveSfMVisibilityCB
                    text: "Live Reconstruction"
                    checkable: true
                    checked: false
                }
                MenuItem {
                    id: imageViewerVisibilityCB
                    text: "Image Viewer"
                    checkable: true
                    checked: true
                }
                MenuItem {
                    id: viewer3DVisibilityCB
                    text: "3D Viewer"
                    checkable: true
                    checked: true
                }
                MenuSeparator {}
                Action {
                    text: "Fullscreen"
                    checkable: true
                    checked: _window.visibility == ApplicationWindow.FullScreen
                    shortcut: "Ctrl+F"
                    onTriggered: _window.visibility == ApplicationWindow.FullScreen ? _window.showNormal() : showFullScreen()
                }
            }
            Menu {
                title: "Process"
                Action {
                    text: "Compute all nodes"
                    onTriggered: computeManager.compute(null)
                    enabled: _reconstruction ? !_reconstruction.computingLocally : false
                }
                Action {
                    text: "Submit all nodes"
                    onTriggered: computeManager.submit(null)
                    enabled: _reconstruction ? _reconstruction.canSubmit : false
                }
                MenuSeparator {}
                Action {
                    text: "Stop computation"
                    onTriggered: _reconstruction.stopExecution()
                    enabled: _reconstruction ? _reconstruction.computingLocally : false
                }
            }
            Menu {
                title: "Help"
                Action {
                    text: "Online Documentation"
                    onTriggered: Qt.openUrlExternally("https://meshroom-manual.readthedocs.io")
                }
                Action {
                    text: "About Meshroom"
                    onTriggered: aboutDialog.open()
                    // should be StandardKey.HelpContents, but for some reason it's not stable
                    // (may cause crash, requires pressing F1 twice after closing the popup)
                    shortcut: "F1"
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: Qt.darker(activePalette.window, 1.15)
        }

        Row {
            // Process buttons
            MaterialToolButton {
                id: processButton

                font.pointSize: 18

                text: !(_reconstruction.computingLocally) ? MaterialIcons.send : MaterialIcons.cancel_schedule_send

                ToolTip.text: !(_reconstruction.computingLocally) ? "Start the computation" : "Stop the computation"
                ToolTip.visible: hovered

                background: Rectangle {
                    color: processButton.hovered ? activePalette.highlight : Qt.darker(activePalette.window, 1.15)
                    border.color: Qt.darker(activePalette.window, 1.15)
                }

                onClicked: !(_reconstruction.computingLocally) ? computeManager.compute(null) : _reconstruction.stopExecution()
            }

            MaterialToolButton {
                id: submitButton

                font.pointSize: 18

                visible: _reconstruction ? _reconstruction.canSubmit : false
                text: MaterialIcons.rocket_launch

                ToolTip.text: "Submit"
                ToolTip.visible: hovered

                background: Rectangle {
                    color: submitButton.hovered ? activePalette.highlight : Qt.darker(activePalette.window, 1.15)
                    border.color: Qt.darker(activePalette.window, 1.15)
                }

                onClicked: computeManager.submit(null)
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: Qt.darker(activePalette.window, 1.15)
        }

        // CompatibilityManager indicator
        ToolButton {
            id: compatibilityIssuesButton
            visible: compatibilityManager.issueCount
            text: MaterialIcons.warning
            font.family: MaterialIcons.fontFamily
            palette.buttonText: "#FF9800"
            font.pointSize: 12
            onClicked: compatibilityManager.open()
            ToolTip.text: "Compatibility Issues"
            ToolTip.visible: hovered

            background: Rectangle {
                color: compatibilityIssuesButton.hovered ? activePalette.highlight : Qt.darker(activePalette.window, 1.15)
                border.color: Qt.darker(activePalette.window, 1.15)
            }
        }
    }

    footer: ToolBar {
        id: footer
        padding: 1
        leftPadding: 4
        rightPadding: 4
        palette.window: Qt.darker(activePalette.window, 1.15)

        // Cache Folder
        RowLayout {
            spacing: 0
            MaterialToolButton {
                font.pointSize: 8
                text: MaterialIcons.folder_open
                ToolTip.text: "Open Cache Folder"
                onClicked: Qt.openUrlExternally(Filepath.stringToUrl(_reconstruction.graph.cacheDir))
            }

            TextField {
                readOnly: true
                selectByMouse: true
                text: _reconstruction ? _reconstruction.graph.cacheDir : "Unknown"
                color: Qt.darker(palette.text, 1.2)
                background: Item {}
            }
        }
    }

    Connections {
        target: _reconstruction

        // Bind messages to DialogsFactory
        function createDialog(func, message)
        {
            var dialog = func(_window)
            // Set text afterwards to avoid dialog sizing issues
            dialog.title = message.title
            dialog.text = message.text
            dialog.detailedText = message.detailedText
        }

        function onGraphChanged() {
            // open CompatibilityManager after file loading if any issue is detected
            if (compatibilityManager.issueCount)
                compatibilityManager.open()
            // trigger fit to visualize all nodes
            graphEditor.fit()
        }

        function onInfo() { createDialog(dialogsFactory.info, arguments[0]) }
        function onWarning() { createDialog(dialogsFactory.warning, arguments[0]) }
        function onError() { createDialog(dialogsFactory.error, arguments[0]) }
    }

    Controls1.SplitView {
        anchors.fill: parent
        orientation: Qt.Vertical

        // Setup global tooltip style
        ToolTip.toolTip.background: Rectangle { color: activePalette.base; border.color: activePalette.mid }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            implicitHeight: Math.round(parent.height * 0.7)
            spacing: 4

            // "ProgressBar" reflecting status of all the chunks in the graph, in their process order
            NodeChunks {
                id: chunksListView
                Layout.fillWidth: true
                height: 6
                model: _reconstruction ? _reconstruction.sortedDFSChunks : null
                highlightChunks: false
            }

            WorkspaceView {
                id: workspaceView
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumHeight: 50
                reconstruction: _reconstruction
                readOnly: _reconstruction ? _reconstruction.computing : false

                function viewNode(node, mouse) {
                    // 2D viewer
                    viewer2D.tryLoadNode(node)

                    // 3D viewer
                    // By default we only display the first 3D item, except if it has the semantic flag "3D"
                    var alreadyDisplay = false
                    for (var i = 0; i < node.attributes.count; i++) {
                        var attr = node.attributes.at(i)
                        if (attr.isOutput && attr.desc.semantic !== "image")
                            if (!alreadyDisplay || attr.desc.semantic == "3D")
                                if (workspaceView.viewIn3D(attr, mouse))
                                      alreadyDisplay = true
                        }
                }

                function viewIn3D(attribute, mouse) {
                    if (!panel3dViewer || (!attribute.node.has3DOutput && !attribute.node.hasAttribute("useBoundingBox")))
                        return false
                    var loaded = panel3dViewer.viewer3D.view(attribute)

                    // solo media if Control modifier was held
                    if (loaded && mouse && mouse.modifiers & Qt.ControlModifier)
                        panel3dViewer.viewer3D.solo(attribute)
                    return loaded
                }
            }
        }

        Controls1.SplitView {
            orientation: Qt.Horizontal
            width: parent.width
            height: Math.round(parent.height * 0.3)
            visible: settings_UILayout.showGraphEditor

            TabPanel {
                id: graphEditorPanel
                Layout.fillWidth: true
                padding: 4
                tabs: ["Graph Editor", "Task Manager", "Script Editor"]

                headerBar: RowLayout {
                    MaterialToolButton {
                        text: MaterialIcons.refresh
                        ToolTip.text: "Refresh Nodes Status"
                        ToolTip.visible: hovered
                        font.pointSize: 11
                        padding: 2
                        onClicked: {
                            updatingStatus = true
                            _reconstruction.forceNodesStatusUpdate()
                            updatingStatus = false
                        }
                        property bool updatingStatus: false
                        enabled: !updatingStatus
                    }
                    MaterialToolButton {
                        id: filePollerRefreshStatus
                        text: {
                            if (_reconstruction.filePollerRefresh === 0)
                                return MaterialIcons.published_with_changes
                            else if (_reconstruction.filePollerRefresh === 2)
                                return MaterialIcons.sync
                            else
                                return MaterialIcons.sync_disabled
                        }
                        font.pointSize: 11
                        padding: 2
                        enabled: true
                        ToolTip {
                            id: filePollerTooltip
                            property string title: "Auto-Refresh Nodes Status For External Changes. "
                            property string description: "Check if the status of a node is changed by another instance on the same network, " +
                                                         "such as when computing in render farm."
                            text: {
                                var status = ""
                                if (_reconstruction.filePollerRefresh === 0)
                                    status = "Enabled"
                                else if (_reconstruction.filePollerRefresh === 2)
                                    status = "Minimal"
                                else
                                    status = "Disabled"
                                return title + "(Current: " + status + ")\n\n" + description
                            }
                            visible: filePollerRefreshStatus.hovered
                            contentWidth: 420
                        }
                        onClicked: {
                            refreshFilesMenu.open()
                        }
                        Menu {
                            id: refreshFilesMenu
                            width: 210
                            y: parent.height
                            x: -width + parent.width
                            MenuItem {
                                id: enableAutoRefresh
                                text: "Enable Auto-Refresh"
                                checkable: true
                                checked: _reconstruction.filePollerRefresh === 0
                                ToolTip.text: "Check every file's status periodically"
                                ToolTip.visible: hovered
                                ToolTip.delay: 200
                                onToggled: {
                                    if (checked) {
                                        disableAutoRefresh.checked = false
                                        minimalAutoRefresh.checked = false
                                        _reconstruction.filePollerRefreshChanged(0)
                                    }
                                    // Prevents cases where the user unchecks the currently checked option
                                    enableAutoRefresh.checked = true
                                    filePollerRefreshStatus.text = MaterialIcons.published_with_changes
                                    filePollerTooltip.text = filePollerTooltip.title + "(Current: Enabled)\n\n" + filePollerTooltip.description
                                }
                            }
                            MenuItem {
                                id: disableAutoRefresh
                                text: "Disable Auto-Refresh"
                                checkable: true
                                checked: _reconstruction.filePollerRefresh === 1
                                ToolTip.text: "No file status will be checked"
                                ToolTip.visible: hovered
                                ToolTip.delay: 200
                                onToggled: {
                                    if (checked) {
                                        enableAutoRefresh.checked = false
                                        minimalAutoRefresh.checked = false
                                        _reconstruction.filePollerRefreshChanged(1)
                                    }
                                    // Prevents cases where the user unchecks the currently checked option
                                    disableAutoRefresh.checked = true
                                    filePollerRefreshStatus.text = MaterialIcons.sync_disabled
                                    filePollerTooltip.text = filePollerTooltip.title + "(Current: Disabled)\n\n" + filePollerTooltip.description
                                }
                            }
                            MenuItem {
                                id: minimalAutoRefresh
                                text: "Enable Minimal Auto-Refresh"
                                checkable: true
                                checked: _reconstruction.filePollerRefresh === 2
                                ToolTip.text: "Check the file status of submitted or running chunks periodically"
                                ToolTip.visible: hovered
                                ToolTip.delay: 200
                                onToggled: {
                                    if (checked) {
                                        disableAutoRefresh.checked = false
                                        enableAutoRefresh.checked = false
                                        _reconstruction.filePollerRefreshChanged(2)
                                    }
                                    // Prevents cases where the user unchecks the currently checked option
                                    minimalAutoRefresh.checked = true
                                    filePollerRefreshStatus.text = MaterialIcons.sync
                                    filePollerTooltip.text = filePollerTooltip.title + "(Current: Minimal)\n\n" + filePollerTooltip.description
                                }
                            }
                        }
                    }
                    MaterialToolButton {
                        text: MaterialIcons.more_vert
                        font.pointSize: 11
                        padding: 2
                        onClicked: graphEditorMenu.open()
                        checkable: true
                        checked: graphEditorMenu.visible
                        Menu {
                            id: graphEditorMenu
                            y: parent.height
                            x: -width + parent.width
                            MenuItem {
                                text: "Clear Pending Status"
                                enabled: _reconstruction ? !_reconstruction.computingLocally : false
                                onTriggered: _reconstruction.graph.clearSubmittedNodes()
                            }
                            MenuItem {
                                text: "Force Unlock Nodes"
                                onTriggered: _reconstruction.graph.forceUnlockNodes()
                            }
                        }
                    }
                }

                GraphEditor {
                    id: graphEditor

                    visible: graphEditorPanel.currentTab === 0

                    anchors.fill: parent
                    uigraph: _reconstruction
                    nodeTypesModel: _nodeTypes

                    onNodeDoubleClicked: {
                        _reconstruction.setActiveNode(node);
                        workspaceView.viewNode(node, mouse);
                    }
                    onComputeRequest: {
                        _reconstruction.forceNodesStatusUpdate();
                        computeManager.compute(nodes)
                    }
                    onSubmitRequest: {
                        _reconstruction.forceNodesStatusUpdate();
                        computeManager.submit(nodes)
                    }
                    onFilesDropped: {
                        var filesByType = _reconstruction.getFilesByTypeFromDrop(drop.urls)
                        if (filesByType["meshroomScenes"].length == 1) {
                            ensureSaved(function() {
                                if (_reconstruction.handleFilesUrl(filesByType, null, mousePosition)) {
                                    MeshroomApp.addRecentProjectFile(filesByType["meshroomScenes"][0])
                                }
                            })
                        } else {
                            _reconstruction.handleFilesUrl(filesByType, null, mousePosition)
                        }
                    }
                }

                TaskManager {
                    id: taskManager

                    visible: graphEditorPanel.currentTab === 1

                    uigraph: _reconstruction
                    taskManager: _reconstruction ? _reconstruction.taskManager : null

                    anchors.fill: parent
                }

                ScriptEditor {
                    id: scriptEditor

                    visible: graphEditorPanel.currentTab === 2
                    anchors.fill: parent
                }
            }

            NodeEditor {
                id: nodeEditor
                width: Math.round(parent.width * 0.3)
                node: _reconstruction ? _reconstruction.selectedNode : null
                property bool computing: _reconstruction ? _reconstruction.computing : false
                // Make NodeEditor readOnly when computing
                readOnly: node ? node.locked : false

                onUpgradeRequest: {
                    var n = _reconstruction.upgradeNode(node)
                    _reconstruction.selectedNode = n
                }
            }
        }
    }
}