import QtQuick 2.7
import QtQuick.Controls 2.3
import QtQuick.Controls 1.4 as Controls1 // For SplitView
import QtQuick.Layouts 1.1
import QtQuick.Window 2.3
import QtQml.Models 2.2

import Qt.labs.platform 1.0 as Platform
import QtQuick.Dialogs 1.3

import Qt.labs.settings 1.0
import GraphEditor 1.0
import MaterialIcons 2.2
import Utils 1.0
import Controls 1.0

ApplicationWindow {
    id: _window

    width: settings_General.windowWidth
    height: settings_General.windowHeight
    minimumWidth: 650
    minimumHeight: 500
    visible: true

    title: {
        var t = (_reconstruction.graph && _reconstruction.graph.filepath) ? _reconstruction.graph.filepath : "Untitled"
        if(!_reconstruction.undoStack.clean)
            t += "*"
        t += " - " + Qt.application.name + " " + Qt.application.version
        return t
    }

    onClosing: {
        // make sure document is saved before exiting application
        close.accepted = false
        if(!ensureNotComputing())
            return
        ensureSaved(function(){ Qt.quit() })
    }

    // force Application palette assignation
    // note: should be implicit (PySide bug)
    palette: _PaletteManager.palette

    SystemPalette { id: activePalette }
    SystemPalette { id: disabledPalette; colorGroup: SystemPalette.Disabled }

    Settings {
        id: settings_General
        category: 'General'
        property int windowWidth: 1280
        property int windowHeight: 720
    }

    Settings {
        id: settings_UILayout
        category: 'UILayout'
        property alias showLiveReconstruction: liveSfMVisibilityCB.checked
        property alias showGraphEditor: graphEditorVisibilityCB.checked
    }

    Component.onDestruction: {
        // store main window dimensions in persisting Settings
        settings_General.windowWidth = _window.width
        settings_General.windowHeight = _window.height
    }

    MessageDialog {
        id: unsavedDialog

        property var _callback: undefined

        title: Filepath.basename(_reconstruction.graph.filepath) || "Unsaved Project"
        preset: "Info"
        canCopy: false
        text: _reconstruction.graph.filepath ? "Current project has unsaved modifications."
                                             : "Current project has not been saved."
        helperText: _reconstruction.graph.filepath ? "Would you like to save those changes?"
                                                   : "Would you like to save this project?"

        standardButtons: Dialog.Save | Dialog.Cancel | Dialog.Discard

        onDiscarded: {
            close() // BUG ? discard does not close window
            fireCallback()
        }

        onAccepted: {
            // save current file
            if(saveAction.enabled)
            {
                saveAction.trigger()
                fireCallback()
            }
            // open "save as" dialog
            else
            {
                saveFileDialog.open()
                function _callbackWrapper(rc) {
                    if(rc == Platform.Dialog.Accepted)
                        fireCallback()
                    saveFileDialog.closed.disconnect(_callbackWrapper)
                }
                saveFileDialog.closed.connect(_callbackWrapper)
            }
        }

        function fireCallback()
        {
            // call the callback and reset it
            if(_callback)
                _callback()
            _callback = undefined
        }

        /// Open the unsaved dialog warning with an optional
        /// callback to fire when the dialog is accepted/discarded
        function prompt(callback)
        {
            _callback = callback
            open()
        }
    }

    Platform.FileDialog {
        id: saveFileDialog

        signal closed(var result)

        title: "Save File"
        nameFilters: ["Meshroom Graphs (*.mg)"]
        defaultSuffix: ".mg"
        fileMode: Platform.FileDialog.SaveFile
        onAccepted: {
            _reconstruction.saveAs(file)
            closed(Platform.Dialog.Accepted)
            MeshroomApp.addRecentProjectFile(file.toString())
        }
        onRejected: closed(Platform.Dialog.Rejected)
    }

    Item {
        id: computeManager

        property bool warnIfUnsaved: true

        // evaluate if global reconstruction computation can be started
        property bool canStartComputation: _reconstruction.viewpoints.count >= 2      // at least 2 images
                                           && !_reconstruction.computing              // computation is not started
                                           && _reconstruction.graph.canComputeLeaves  // graph has no uncomputable nodes

        // evaluate if graph computation can be submitted externally
        property bool canSubmit: _reconstruction.canSubmit                            // current setup allows to compute externally
                                 && canStartComputation                               // can be computed
                                 && _reconstruction.graph.filepath                    // graph is saved on disk

        function compute(node, force) {
            if(!force && warnIfUnsaved && !_reconstruction.graph.filepath)
            {
                unsavedComputeDialog.currentNode = node;
                unsavedComputeDialog.open();
            }
            else {
                try {
                    _reconstruction.execute(node)
                }
                catch (error) {
                    const data = ErrorHandler.analyseError(error)
                    if(data.context === "COMPUTATION")
                        computeSubmitErrorDialog.openError(data.type, data.msg, node)
                }
            }
        }

        function submit(node) {
            try {
                _reconstruction.submit(node)
            }
            catch (error) {
                const data = ErrorHandler.analyseError(error)
                if(data.context === "SUBMITTING")
                    computeSubmitErrorDialog.openError(data.type, data.msg, node)
            }
        }

        MessageDialog {
            id: computeSubmitErrorDialog

            property string errorType // Used to specify signals' behavior
            property var currentNode: null

            function openError(type, msg, node) {
                errorType = type
                switch(type) {
                    case "Already Submitted": this.setupPendingStatusError(msg, node); break
                    case "Compatibility Issue": this.setupCompatibilityIssue(msg); break
                    default: this.onlyDisplayError(msg)
                }

                this.open()
            }

            function onlyDisplayError(msg) {
                text = msg

                standardButtons = Dialog.Ok
            }

            function setupPendingStatusError(msg, node) {
                currentNode = node
                text = msg + "\n\nDo you want to Clear Pending Status and Start Computing?"

                standardButtons = (Dialog.Ok | Dialog.Cancel)
            }

            function setupCompatibilityIssue(msg) {
                text = msg + "\n\nDo you want to open the Compatibility Manager?"

                standardButtons = (Dialog.Ok | Dialog.Cancel)
            }

            canCopy: false
            icon.text: MaterialIcons.warning
            parent: Overlay.overlay
            preset: "Warning"
            title: "Computation/Submitting"
            text: ""

            onAccepted: {
                switch(errorType) {
                    case "Already Submitted": {
                        close()
                        _reconstruction.graph.clearSubmittedNodes()
                        _reconstruction.execute(currentNode)
                        break
                    }
                    case "Compatibility Issue": {
                        close()
                        compatibilityManager.open()
                    }
                    default: close()
                }
            }

            onRejected: close()
        }

        MessageDialog {
            id: unsavedComputeDialog

            property var currentNode: null

            canCopy: false
            icon.text: MaterialIcons.warning
            parent: Overlay.overlay
            preset: "Warning"
            title: "Unsaved Project"
            text: "Data will be computed in the default cache folder if project remains unsaved."
            detailedText: "Default cache folder: " + _reconstruction.graph.cacheDir
            helperText: "Save project first?"
            standardButtons: Dialog.Discard | Dialog.Cancel | Dialog.Save

            CheckBox {
                Layout.alignment: Qt.AlignRight
                text: "Don't ask again for this session"
                padding: 0
                onToggled: computeManager.warnIfUnsaved = !checked
            }

            Component.onCompleted: {
                // set up discard button text
                standardButton(Dialog.Discard).text = "Continue without Saving"
            }

            onDiscarded: { close(); computeManager.compute(currentNode, true) }
            onAccepted: saveAsAction.trigger()
        }
    }

    FileDialog {
        id: openFileDialog
        title: "Open File"
        nameFilters: ["Meshroom Graphs (*.mg)"]
        onAccepted: {
            if(_reconstruction.loadUrl(fileUrl))
            {
                MeshroomApp.addRecentProjectFile(fileUrl.toString())
            }
        }
    }

    FileDialog {
        id: importFilesDialog
        title: "Import Images"
        selectExisting: true
        selectMultiple: true
        nameFilters: []
        onAccepted: {
            console.warn("importFilesDialog fileUrls: " + importFilesDialog.fileUrls)
            _reconstruction.importImagesUrls(importFilesDialog.fileUrls)
        }
    }

    AboutDialog {
        id: aboutDialog
    }

    // Check if document has been saved
    function ensureSaved(callback)
    {
        var saved = _reconstruction.undoStack.clean
        // If current document is modified, open "unsaved dialog"
        if(!saved)
        {
            unsavedDialog.prompt(callback)
        }
        else // otherwise, directly call the callback
        {
            callback()
        }
        return saved
    }

    MessageDialog {
        id: computingAtExitDialog
        title: "Operation in progress"
        modal: true
        canCopy: false
        Label {
            text: "Please stop any local computation before exiting Meshroom"
        }
    }

    // Check and return whether no local computation is in progress
    function ensureNotComputing()
    {
        if(_reconstruction.computingLocally)
        {
            // Open a warning dialog to ask for computation to be stopped
            computingAtExitDialog.open()
            return false
        }
        return true
    }

    MessageDialog {
        // Popup displayed while the application
        // is busy building intrinsics while importing images
        id: buildingIntrinsicsDialog
        modal: true
        visible: _reconstruction.buildingIntrinsics
        closePolicy: Popup.NoAutoClose
        title: "Initializing Cameras"
        icon.text: MaterialIcons.camera
        icon.font.pointSize: 10
        canCopy: false
        standardButtons: Dialog.NoButton

        detailedText:  "Extracting images metadata and creating Camera intrinsics..."
        ProgressBar {
            indeterminate: true
            Layout.fillWidth: true
        }
    }

    DialogsFactory {
        id: dialogsFactory
    }

    CompatibilityManager {
        id: compatibilityManager
        uigraph: _reconstruction
    }

    Action {
        id: undoAction

        property string tooltip: 'Undo "' +_reconstruction.undoStack.undoText +'"'
        text: "Undo"
        shortcut: "Ctrl+Z"
        enabled: _reconstruction.undoStack.canUndo && _reconstruction.undoStack.isUndoableIndex
        onTriggered: _reconstruction.undoStack.undo()
    }
    Action {
        id: redoAction

        property string tooltip: 'Redo "' +_reconstruction.undoStack.redoText +'"'
        text: "Redo"
        shortcut: "Ctrl+Shift+Z"
        enabled: _reconstruction.undoStack.canRedo && !_reconstruction.undoStack.lockedRedo
        onTriggered: _reconstruction.undoStack.redo()
    }

    Action {
        shortcut: "Ctrl+Shift+P"
        onTriggered: _PaletteManager.togglePalette()
    }

    header: MenuBar {
        palette.window: Qt.darker(activePalette.window, 1.15)
        Menu {
            title: "File"
            Action {
                text: "New"
                shortcut: "Ctrl+N"
                onTriggered: ensureSaved(function() { _reconstruction.new() })
            }
            Menu {
                title: "New Pipeline"
                TextMetrics {
                    id: textMetrics
                    font: action_PG_CT.font
                    elide: Text.ElideNone
                    text: action_PG_CT.text
                }
                implicitWidth: textMetrics.width + 10  // largest text width + margin
                Action {
                    text: "Photogrammetry"
                    onTriggered: ensureSaved(function() { _reconstruction.new("photogrammetry") })
                }
                Action {
                    text: "Panorama HDR"
                    onTriggered: ensureSaved(function() { _reconstruction.new("panoramahdr") })
                }
                Action {
                    text: "Panorama Fisheye HDR"
                    onTriggered: ensureSaved(function() { _reconstruction.new("panoramafisheyehdr") })
                }
                Action {
                    id: action_PG_CT
                    text: "Photogrammetry and Camera Tracking (experimental)"
                    onTriggered: ensureSaved(function() { _reconstruction.new("photogrammetryandcameratracking") })
                }
                Action {
                    text: "Camera Tracking (experimental)"
                    onTriggered: ensureSaved(function() { _reconstruction.new("cameratracking") })
                }
            }
            Action {
                id: openActionItem
                text: "Open"
                shortcut: "Ctrl+O"
                onTriggered: ensureSaved(function() {
                        if(_reconstruction.graph && _reconstruction.graph.filepath) {
                            openFileDialog.folder = Filepath.stringToUrl(Filepath.dirname(_reconstruction.graph.filepath))
                        }
                        openFileDialog.open()
                    })
            }
            Menu {
                id: openRecentMenu
                title: "Open Recent"
                enabled: recentFilesMenuItems.model != undefined && recentFilesMenuItems.model.length > 0
                property int maxWidth: 1000
                property int fullWidth: {
                    var result = 0;
                    for (var i = 0; i < count; ++i) {
                        var item = itemAt(i);
                        result = Math.max(item.implicitWidth + item.padding * 2, result);
                    }
                    return result;
                }
                implicitWidth: fullWidth
                Repeater {
                    id: recentFilesMenuItems
                    model: MeshroomApp.recentProjectFiles
                    MenuItem {
                        onTriggered: ensureSaved(function() {
                            openRecentMenu.dismiss();
                            if(_reconstruction.loadUrl(modelData))
                            {
                                MeshroomApp.addRecentProjectFile(modelData);
                            }
                            else
                            {
                                MeshroomApp.removeRecentProjectFile(modelData);
                            }
                        })
                        
                        text: fileTextMetrics.elidedText
                        TextMetrics {
                            id: fileTextMetrics
                            text: modelData
                            elide: Text.ElideLeft
                            elideWidth: openRecentMenu.maxWidth
                        }
                    }
                }
            }
            Action {
                id: importActionItem
                text: "Import Images"
                shortcut: "Ctrl+I"
                onTriggered: importFilesDialog.open()
            }

            Action {
                id: clearActionItem
                text: "Clear Images"
                onTriggered: {
                    //Loop through all the camera inits
                    for(var i = 0 ; i < _reconstruction.cameraInits.count; i++){
                        var cameraInit = _reconstruction.cameraInits.at(i)

                        //Delete all viewpoints
                        var viewpoints = cameraInit.attribute('viewpoints')
                        for(var y = viewpoints.value.count - 1 ; y >= 0 ; y--){
                              _reconstruction.removeAttribute(viewpoints.value.at(y))
                        }

                        //Delete all intrinsics
                        var intrinsics = cameraInit.attribute('intrinsics')
                        for(var z = intrinsics.value.count - 1 ; z >= 0 ; z--){
                              _reconstruction.removeAttribute(intrinsics.value.at(z))
                        }
                    }
                }
            }

            Action {
                id: saveAction
                text: "Save"
                shortcut: "Ctrl+S"
                enabled: (_reconstruction.graph && !_reconstruction.graph.filepath) || !_reconstruction.undoStack.clean
                onTriggered: {
                    if(_reconstruction.graph.filepath) {
                        _reconstruction.save()
                    }
                    else
                    {
                        saveFileDialog.open()
                    }
                }
            }
            Action {
                id: saveAsAction
                text: "Save As..."
                shortcut: "Ctrl+Shift+S"
                onTriggered: {
                    if(_reconstruction.graph && _reconstruction.graph.filepath) {
                        saveFileDialog.folder = Filepath.stringToUrl(Filepath.dirname(_reconstruction.graph.filepath))
                    }
                    saveFileDialog.open()
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
            title: "Help"
            Action {
                text: "Online Documentation"
                onTriggered: Qt.openUrlExternally("https://meshroom-manual.readthedocs.io")
            }
            Action {
                text: "About Meshroom"
                onTriggered: aboutDialog.open()
                // shoud be StandardKey.HelpContents, but for some reason it's not stable
                // (may cause crash, requires pressing F1 twice after closing the popup)
                shortcut: "F1"
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
                text: _reconstruction.graph.cacheDir
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

        onGraphChanged: {
            // open CompatibilityManager after file loading if any issue is detected
            if(compatibilityManager.issueCount)
                compatibilityManager.open()
            // trigger fit to visualize all nodes
            graphEditor.fit()
        }

        onInfo: createDialog(dialogsFactory.info, arguments[0])
        onWarning: createDialog(dialogsFactory.warning, arguments[0])
        onError: createDialog(dialogsFactory.error, arguments[0])
    }


    Controls1.SplitView {
        anchors.fill: parent
        orientation: Qt.Vertical

        // Setup global tooltip style
        ToolTip.toolTip.background: Rectangle { color: activePalette.base; border.color: activePalette.mid }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.topMargin: 2
            implicitHeight: Math.round(parent.height * 0.7)
            spacing: 4
            RowLayout {
                Layout.rightMargin: 4
                Layout.leftMargin: 4
                Layout.fillHeight: false
                Item { Layout.fillWidth: true }

                Row {
                    // disable controls if graph is executed externally
                    Layout.alignment: Qt.AlignHCenter

                    Button {
                        property color buttonColor: Qt.darker("#4CAF50", 1.8)
                        text: "Start"
                        palette.button: enabled ? buttonColor : disabledPalette.button
                        palette.window: enabled ? buttonColor : disabledPalette.window
                        palette.buttonText: enabled ? "white" : disabledPalette.buttonText
                        onClicked: computeManager.compute(null)
                    }
                    Button {
                        text: "Stop"
                        enabled: _reconstruction.computingLocally
                        onClicked: _reconstruction.stopExecution()
                    }
                    Item { width: 20; height: 1 }
                    Button {
                        visible: _reconstruction.canSubmit
                        text: "Submit"
                        onClicked: computeManager.submit(null)
                    }
                }
                Item { Layout.fillWidth: true; Layout.fillHeight: true }

                // CompatibilityManager indicator
                ToolButton {
                    visible: compatibilityManager.issueCount
                    text: MaterialIcons.warning
                    font.family: MaterialIcons.fontFamily
                    palette.buttonText: "#FF9800"
                    font.pointSize: 12
                    onClicked: compatibilityManager.open()
                    ToolTip.text: "Compatibility Issues"
                    ToolTip.visible: hovered
                }
            }

            // "ProgressBar" reflecting status of all the chunks in the graph, in their process order
            NodeChunks {
                id: chunksListView
                Layout.fillWidth: true
                height: 6
                model: _reconstruction.sortedDFSChunks
            }

            WorkspaceView {
                id: workspaceView
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumHeight: 50
                reconstruction: _reconstruction
                readOnly: _reconstruction.computing

                function viewAttribute(attribute, mouse) {
                    let viewable = false;
                    viewable = workspaceView.viewIn2D(attribute);
                    viewable |= workspaceView.viewIn3D(attribute, mouse);
                    return viewable;
                }

                function viewIn3D(attribute, mouse) {
                    var loaded = viewer3D.view(attribute);
                    // solo media if Control modifier was held
                    if(loaded && mouse && mouse.modifiers & Qt.ControlModifier)
                        viewer3D.solo(attribute);
                    return loaded;
                }

                function viewIn2D(attribute) {
                    var imageExts = ['.exr', '.jpg', '.tif', '.png'];
                    var ext = Filepath.extension(attribute.value);
                    if(imageExts.indexOf(ext) == -1)
                    {
                        return false;
                    }

                    if(attribute.value.includes('*'))
                    {
                        // For now, the viewer only supports a single image.
                        var firstFile = Filepath.globFirst(attribute.value)
                        viewer2D.source = Filepath.stringToUrl(firstFile);
                    }
                    else
                    {
                        viewer2D.source = Filepath.stringToUrl(attribute.value);
                        return true;
                    }

                    return false;
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
                tabs: ["Graph Editor", "Task Manager"]

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
                        enabled: !updatingStatus && !_reconstruction.computingLocally
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
                                enabled: !_reconstruction.computingLocally
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

                        let viewable = false;
                        for(var i=0; i < node.attributes.count; ++i)
                        {
                            var attr = node.attributes.at(i)
                            if(attr.isOutput && workspaceView.viewAttribute(attr, mouse))
                                break;
                        }
                    }
                    onComputeRequest: computeManager.compute(node)
                    onSubmitRequest: computeManager.submit(node)
                }

                TaskManager {
                    id: taskManager

                    visible: graphEditorPanel.currentTab === 1

                    uigraph: _reconstruction
                    taskManager: _reconstruction.taskManager

                    anchors.fill: parent
                }

            }

            NodeEditor {
                id: nodeEditor
                width: Math.round(parent.width * 0.3)
                node: _reconstruction.selectedNode
                property bool computing: _reconstruction.computing
                // Make NodeEditor readOnly when computing
                readOnly: node ? node.locked : false

                onAttributeDoubleClicked: workspaceView.viewAttribute(attribute, mouse)
                onUpgradeRequest: {
                    var n = _reconstruction.upgradeNode(node);
                    _reconstruction.selectedNode = n;
                }
            }
        }
    }
 }
