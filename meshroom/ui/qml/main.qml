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

ApplicationWindow {
    id: _window

    width: settings_General.windowWidth
    height: settings_General.windowHeight
    minimumWidth: 650
    minimumHeight: 500
    visible: true

    title: {
        var t = (_reconstruction && _reconstruction.graph && _reconstruction.graph.filepath) ? _reconstruction.graph.filepath : "Untitled"
        if (_reconstruction && !_reconstruction.undoStack.clean)
            t += "*"
        t += " - " + Qt.application.name + " " + Qt.application.version
        return t
    }

    onClosing: {
        // make sure document is saved before exiting application
        close.accepted = false
        if (!ensureNotComputing())
            return
        ensureSaved(function() { Qt.quit() })
    }

    palette: _PaletteManager.palette

    // TODO: uncomment for Qt6, which correctly supports palette for disabled elements AND an alternate base
    /*
    // QPalette is not convertible to QML palette (anymore)
    Component.onCompleted: {
        palette.alternateBase = _PaletteManager.alternateBase
        palette.base = _PaletteManager.base
        palette.button = _PaletteManager.button
        palette.buttonText = _PaletteManager.buttonText
        palette.highlight = _PaletteManager.highlight
        palette.highlightedText = _PaletteManager.highlightedText
        palette.link = _PaletteManager.link
        palette.mid = _PaletteManager.mid
        palette.shadow = _PaletteManager.shadow
        palette.text = _PaletteManager.text
        palette.toolTipBase = _PaletteManager.toolTipBase
        palette.toolTipText = _PaletteManager.toolTipText
        palette.window = _PaletteManager.window
        palette.windowText = _PaletteManager.windowText

        palette.disabled.buttonText = _PaletteManager.disabledButtonText
        palette.disabled.highlight = _PaletteManager.disabledHighlight
        palette.disabled.highlightedText = _PaletteManager.disabledHighlightedText
        palette.disabled.text = _PaletteManager.disabledText
        palette.disabled.windowText = _PaletteManager.disabledWindowText
    } */

    SystemPalette { id: activePalette }
    SystemPalette { id: disabledPalette; colorGroup: SystemPalette.Disabled }

    property url imagesFolder: {
        var recentImportedImagesFolders = MeshroomApp.recentImportedImagesFolders
        if (recentImportedImagesFolders.length > 0) {
            for (var i = 0; i < recentImportedImagesFolders.length; i++) {
                if (Filepath.exists(recentImportedImagesFolders[i]))
                    return Filepath.stringToUrl(recentImportedImagesFolders[i])
                else
                    MeshroomApp.removeRecentImportedImagesFolder(Filepath.stringToUrl(recentImportedImagesFolders[i]))
            }
        }
        return ""
    }

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
        property alias showImageViewer: imageViewerVisibilityCB.checked
        property alias showViewer3D: viewer3DVisibilityCB.checked
    }

    Component.onDestruction: {
        // store main window dimensions in persisting Settings
        settings_General.windowWidth = _window.width
        settings_General.windowHeight = _window.height
    }

    Shortcut {
        // Ensures the Ctrl+N shortcut is always valid and creates a default pipeline
        sequence: "Ctrl+N"
        context: Qt.ApplicationShortcut
        onActivated: ensureSaved(function() { _reconstruction.new() })
    }

    MessageDialog {
        id: unsavedDialog

        property var _callback: undefined

        title: (_reconstruction ? Filepath.basename(_reconstruction.graph.filepath) : "") || "Unsaved Project"
        preset: "Info"
        canCopy: false
        text: _reconstruction && _reconstruction.graph.filepath ? "Current project has unsaved modifications."
                                             : "Current project has not been saved."
        helperText: _reconstruction && _reconstruction.graph.filepath ? "Would you like to save those changes?"
                                                   : "Would you like to save this project?"

        standardButtons: Dialog.Save | Dialog.Cancel | Dialog.Discard

        onDiscarded: {
            close() // BUG ? discard does not close window
            fireCallback()
        }

        onAccepted: {
            // save current file
            if (saveAction.enabled)
            {
                saveAction.trigger()
                fireCallback()
            }
            // open "save as" dialog
            else
            {
                saveFileDialog.open()
                function _callbackWrapper(rc) {
                    if (rc === Platform.Dialog.Accepted)
                        fireCallback()
                    saveFileDialog.closed.disconnect(_callbackWrapper)
                }
                saveFileDialog.closed.connect(_callbackWrapper)
            }
        }

        function fireCallback()
        {
            // call the callback and reset it
            if (_callback)
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

    Platform.FileDialog {
        id: saveTemplateDialog

        signal closed(var result)

        title: "Save Template"
        nameFilters: ["Meshroom Graphs (*.mg)"]
        defaultSuffix: ".mg"
        fileMode: Platform.FileDialog.SaveFile
        onAccepted: {
            _reconstruction.saveAsTemplate(file)
            closed(Platform.Dialog.Accepted)
            MeshroomApp.reloadTemplateList()
        }
        onRejected: closed(Platform.Dialog.Rejected)
    }

    Item {
        id: computeManager

        property bool warnIfUnsaved: true

        // evaluate if graph computation can be submitted externally
        property bool canSubmit: _reconstruction ?
                                 _reconstruction.canSubmit                             // current setup allows to compute externally
                                 && _reconstruction.graph.filepath :                   // graph is saved on disk
                                 false

        function compute(node, force) {
            if (!force && warnIfUnsaved && !_reconstruction.graph.filepath)
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
                    if (data.context === "COMPUTATION")
                        computeSubmitErrorDialog.openError(data.type, data.msg, node)
                }
            }
        }

        function submit(node) {
            if (!canSubmit) {
                unsavedSubmitDialog.open()
            } else {
                try {
                    _reconstruction.submit(node)
                }
                catch (error) {
                    const data = ErrorHandler.analyseError(error)
                    if (data.context === "SUBMITTING")
                        computeSubmitErrorDialog.openError(data.type, data.msg, node)
                }
            }
        }

        MessageDialog {
            id: computeSubmitErrorDialog

            property string errorType // Used to specify signals' behavior
            property var currentNode: null

            function openError(type, msg, node) {
                errorType = type
                switch (type) {
                    case "Already Submitted": {
                            this.setupPendingStatusError(msg, node)
                            break
                    }
                    case "Compatibility Issue": {
                        this.setupCompatibilityIssue(msg)
                        break
                    }
                    default: {
                        this.onlyDisplayError(msg)
                    }
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
                switch (errorType) {
                    case "Already Submitted": {
                        close()
                        _reconstruction.graph.clearSubmittedNodes()
                        _reconstruction.execute(currentNode)
                        break
                    }
                    case "Compatibility Issue": {
                        close()
                        compatibilityManager.open()
                        break
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
            detailedText: "Default cache folder: " + (_reconstruction ? _reconstruction.graph.cacheDir : "unknown")
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

            onDiscarded: {
                close()
                computeManager.compute(currentNode, true)
            }

            onAccepted: saveAsAction.trigger()
        }

        MessageDialog {
            id: unsavedSubmitDialog

            canCopy: false
            icon.text: MaterialIcons.warning
            parent: Overlay.overlay
            preset: "Warning"
            title: "Unsaved Project"
            text: "The project cannot be submitted if it remains unsaved."
            helperText: "Save the project to be able to submit it?"
            standardButtons: Dialog.Cancel | Dialog.Save

            onDiscarded: close()
            onAccepted: saveAsAction.trigger()
        }
    }

    FileDialog {
        id: openFileDialog
        title: "Open File"
        nameFilters: ["Meshroom Graphs (*.mg)"]
        onAccepted: {
            if (_reconstruction.loadUrl(fileUrl)) {
                MeshroomApp.addRecentProjectFile(fileUrl.toString())
            }
        }
    }

    FileDialog {
        id: loadTemplateDialog
        title: "Load Template"
        nameFilters: ["Meshroom Graphs (*.mg)"]
        onAccepted: {
            // Open the template as a regular file
            if (_reconstruction.loadUrl(fileUrl, true, true)) {
                MeshroomApp.addRecentProjectFile(fileUrl.toString())
            }
        }
    }

    FileDialog {
        id: importImagesDialog
        title: "Import Images"
        selectExisting: true
        selectMultiple: true
        nameFilters: []
        onAccepted: {
            _reconstruction.importImagesUrls(importImagesDialog.fileUrls)
            imagesFolder = Filepath.dirname(importImagesDialog.fileUrls[0])
            MeshroomApp.addRecentImportedImagesFolder(imagesFolder)
        }
    }

    FileDialog {
        id: importProjectDialog
        title: "Import Project"
        selectMultiple: false
        nameFilters: ["Meshroom Graphs (*.mg)"]
        onAccepted: {
            graphEditor.uigraph.importProject(importProjectDialog.fileUrl)
        }
    }

    AboutDialog {
        id: aboutDialog
    }

    // Check if document has been saved
    function ensureSaved(callback)
    {
        var saved = _reconstruction.undoStack.clean
        if (!saved) {  // If current document is modified, open "unsaved dialog"
            unsavedDialog.prompt(callback)
        } else {  // Otherwise, directly call the callback
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
        if (_reconstruction.computingLocally)
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
        visible: _reconstruction ? _reconstruction.buildingIntrinsics : false
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
        id: removeAllImagesAction
        property string tooltip: "Remove all the images from the current CameraInit group"
        text: "Remove All Images"
        onTriggered: {
            _reconstruction.removeAllImages()
            _reconstruction.selectedViewId = "-1"
        }
    }

    Action {
        id: removeImagesFromAllGroupsAction
        property string tooltip: "Remove all the images from all the CameraInit groups"
        text: "Remove Images From All CameraInit Nodes"
        onTriggered: {
            _reconstruction.removeImagesFromAllGroups()
            _reconstruction.selectedViewId = "-1"
        }
    }

    Action {
        id: undoAction

        property string tooltip: 'Undo "' + (_reconstruction ? _reconstruction.undoStack.undoText : "Unknown") + '"'
        text: "Undo"
        shortcut: "Ctrl+Z"
        enabled: _reconstruction ? _reconstruction.undoStack.canUndo && _reconstruction.undoStack.isUndoableIndex : false
        onTriggered: _reconstruction.undoStack.undo()
    }
    Action {
        id: redoAction

        property string tooltip: 'Redo "' + (_reconstruction ? _reconstruction.undoStack.redoText : "Unknown") + '"'
        text: "Redo"
        shortcut: "Ctrl+Shift+Z"
        enabled: _reconstruction ? _reconstruction.undoStack.canRedo && !_reconstruction.undoStack.lockedRedo : false
        onTriggered: _reconstruction.undoStack.redo()
    }
    Action {
        id: copyAction

        property string tooltip: {
            var s = "Copy selected node"
            s += (_reconstruction && _reconstruction.selectedNodes.count > 1 ? "s (" : " (") + getSelectedNodesName()
            s += ") to the clipboard"
            return s
        }
        text: "Copy Node" + (_reconstruction && _reconstruction.selectedNodes.count > 1 ? "s " : " ")
        enabled: _reconstruction ? _reconstruction.selectedNodes.count > 0 : false
        onTriggered: graphEditor.copyNodes()

        function getSelectedNodesName()
        {
            if (!_reconstruction)
                return ""
            var nodesName = ""
            for (var i = 0; i < _reconstruction.selectedNodes.count; i++)
            {
                if (nodesName !== "")
                    nodesName += ", "
                var node = _reconstruction.selectedNodes.at(i)
                nodesName += node.name
            }
            return nodesName
        }
    }

    Action {
        id: pasteAction

        property string tooltip: "Paste the clipboard content to the project if it contains valid nodes"
        text: "Paste Node(s)"
        onTriggered: graphEditor.pasteNodes()
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

    // TODO: uncomment for Qt6 to re-enable the alternative palette (the alternative palette and the disabled items currently cannot both be supported)
    /* Action {

        shortcut: "Ctrl+Shift+P"
        onTriggered: _PaletteManager.togglePalette()
    } */


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

    header: MenuBar {
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
                            if (_reconstruction.loadUrl(modelData)) {
                                MeshroomApp.addRecentProjectFile(modelData)
                            } else {
                                MeshroomApp.removeRecentProjectFile(modelData)
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
            MenuSeparator { }
            Action {
                id: saveAction
                text: "Save"
                shortcut: "Ctrl+S"
                enabled: _reconstruction ? (_reconstruction.graph && !_reconstruction.graph.filepath) || !_reconstruction.undoStack.clean : false
                onTriggered: {
                    if (_reconstruction.graph.filepath) {
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
                        enabled: _reconstruction ? _reconstruction.computingLocally : false
                        onClicked: _reconstruction.stopExecution()
                    }
                    Item { width: 20; height: 1 }
                    Button {
                        visible: _reconstruction ? _reconstruction.canSubmit : false
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
                model: _reconstruction ? _reconstruction.sortedDFSChunks : null
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
                    if (!panel3dViewer || !attribute.node.has3DOutput)
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
                        computeManager.compute(node)
                    }
                    onSubmitRequest: {
                        _reconstruction.forceNodesStatusUpdate();
                        computeManager.submit(node)
                    }
                }

                TaskManager {
                    id: taskManager

                    visible: graphEditorPanel.currentTab === 1

                    uigraph: _reconstruction
                    taskManager: _reconstruction ? _reconstruction.taskManager : null

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

    background: MouseArea {
        onPressed: {
            forceActiveFocus();
        }
    }
 }
