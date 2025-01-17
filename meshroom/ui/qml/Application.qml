import QtCore

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQml.Models

import Qt.labs.platform 1.0 as Platform
import QtQuick.Dialogs

import GraphEditor 1.0
import MaterialIcons 2.2
import Utils 1.0
import Controls 1.0

Page {
    id: root

    property alias computingAtExitDialog: computingAtExitDialog
    property alias unsavedDialog: unsavedDialog
    property alias workspaceView: workspaceView

    readonly property var scenefile: _reconstruction ? _reconstruction.graph.filepath : "";

    onScenefileChanged: {
        // Check if we're not currently saving and emit the currentProjectChanged signal
        if (! _reconstruction.graph.isSaving) {
            // Refresh the NodeEditor
            nodeEditor.refresh();
        }
    }

    Settings {
        id: settingsUILayout
        category: "UILayout"
        property alias showLiveReconstruction: liveSfMVisibilityCB.checked
        property alias showGraphEditor: graphEditorVisibilityCB.checked
        property alias showImageViewer: imageViewerVisibilityCB.checked
        property alias showViewer3D: viewer3DVisibilityCB.checked
        property alias showImageGallery: imageGalleryVisibilityCB.checked
    }


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

    Component {
        id: invalidFilepathDialog

        MessageDialog {
            title: "Invalid Filepath"

            required property string filepath

            preset: "Warning"
            text: "The provided filepath is not valid."
            detailedText: "Filepath: " + filepath
            helperText: "Please provide a valid filepath to save the file."

            standardButtons: Dialog.Ok
            onClosed: destroy()
        }
    }

    Component {
        id: permissionsDialog

        MessageDialog {
            title: "Permission Denied"

            required property string filepath

            preset: "Warning"
            text: "The location does not exist or you do not have necessary permissions to save to the provided filepath."
            detailedText: "Filepath: " + filepath
            helperText: "Please check the location or permissions and try again or choose a different location."

            standardButtons: Dialog.Ok
            onClosed: destroy()
        }
    }

    function validateFilepathForSave(filepath: string, sourceSaveDialog: Dialog): bool {
        /**
         * Return true if `filepath` is valid for saving a file to disk.
         * Otherwise, show a warning dialog and returns false.
         * Closing the warning dialog reopens the specified `sourceSaveDialog`, to allow the user to try again.
         */
        const emptyFilename = Filepath.basename(filepath).trim() === ".mg";

        // Provided filename is not valid
        if (emptyFilename) {
            // Instantiate the Warning Dialog with the provided filepath
            const warningDialog = invalidFilepathDialog.createObject(root, {"filepath": Filepath.urlToString(filepath)});

            // And open the dialog
            warningDialog.closed.connect(sourceSaveDialog.open);
            warningDialog.open();

            return false;
        }

        // Check if the user has access to the directory where the file is to be saved
        const hasPermission = Filepath.accessible(Filepath.dirname(filepath));

        // Either the directory does not exist or is inaccessible for the user
        if (!hasPermission) {
            // Intantiate the permissions dialog with the provided filepath
            const warningDialog = permissionsDialog.createObject(root, {"filepath": Filepath.urlToString(filepath)});

            // Connect and show the dialog
            warningDialog.closed.connect(sourceSaveDialog.open);
            warningDialog.open();

            return false;
        }

        // Everything is valid
        return true;
    }

    // File dialogs
    Platform.FileDialog {
        id: saveFileDialog
        options: Platform.FileDialog.DontUseNativeDialog

        signal closed(var result)

        title: "Save File"
        nameFilters: ["Meshroom Graphs (*.mg)"]
        defaultSuffix: ".mg"
        fileMode: Platform.FileDialog.SaveFile
        onAccepted: {
            if (!validateFilepathForSave(currentFile, saveFileDialog))
            {
                return;
            }

            // Only save a valid file
            _reconstruction.saveAs(currentFile)
            MeshroomApp.addRecentProjectFile(currentFile.toString())
            closed(Platform.Dialog.Accepted)
        }
        onRejected: closed(Platform.Dialog.Rejected)
    }

    Platform.FileDialog {
        id: saveTemplateDialog
        options: Platform.FileDialog.DontUseNativeDialog

        signal closed(var result)

        title: "Save Template"
        nameFilters: ["Meshroom Graphs (*.mg)"]
        defaultSuffix: ".mg"
        fileMode: Platform.FileDialog.SaveFile
        onAccepted: {
            if (!validateFilepathForSave(currentFile, saveTemplateDialog))
            {
                return;
            }

            // Only save a valid template
            _reconstruction.saveAsTemplate(currentFile)
            closed(Platform.Dialog.Accepted)
            MeshroomApp.reloadTemplateList()
        }
        onRejected: closed(Platform.Dialog.Rejected)
    }

    Platform.FileDialog {
        id: loadTemplateDialog
        options: Platform.FileDialog.DontUseNativeDialog
        title: "Load Template"
        nameFilters: ["Meshroom Graphs (*.mg)"]
        onAccepted: {
            // Open the template as a regular file
            if (_reconstruction.loadUrl(currentFile, true, true)) {
                MeshroomApp.addRecentProjectFile(currentFile.toString())
            }
        }
    }

    Platform.FileDialog {
        id: importImagesDialog
        options: Platform.FileDialog.DontUseNativeDialog
        title: "Import Images"
        fileMode: Platform.FileDialog.OpenFiles
        nameFilters: []
        onAccepted: {
            _reconstruction.importImagesUrls(currentFiles)
            imagesFolder = Filepath.dirname(currentFiles[0])
            MeshroomApp.addRecentImportedImagesFolder(imagesFolder)
        }
    }

    Platform.FileDialog {
        id: importProjectDialog
        options: Platform.FileDialog.DontUseNativeDialog
        title: "Import Project"
        fileMode: Platform.FileDialog.OpenFile
        nameFilters: ["Meshroom Graphs (*.mg)"]
        onAccepted: {
            graphEditor.uigraph.importProject(currentFile)
        }
    }

    Item {
        id: computeManager

        property bool warnIfUnsaved: true

        // Evaluate if graph computation can be submitted externally
        property bool canSubmit: _reconstruction ?
                                 _reconstruction.canSubmit                 // current setup allows to compute externally
                                 && _reconstruction.graph.filepath :       // graph is saved on disk
                                 false

        function compute(nodes, force) {
            if (!force && warnIfUnsaved && !_reconstruction.graph.filepath) {
                unsavedComputeDialog.selectedNodes = nodes;
                unsavedComputeDialog.open();
            }
            else {
                try {
                    _reconstruction.execute(nodes)
                }
                catch (error) {
                    const data = ErrorHandler.analyseError(error)
                    if (data.context === "COMPUTATION")
                        computeSubmitErrorDialog.openError(data.type, data.msg, nodes)
                }
            }
        }

        function submit(nodes) {
            if (!canSubmit) {
                unsavedSubmitDialog.open()
            } else {
                try {
                    _reconstruction.submit(nodes)
                }
                catch (error) {
                    const data = ErrorHandler.analyseError(error)
                    if (data.context === "SUBMITTING")
                        computeSubmitErrorDialog.openError(data.type, data.msg, nodes)
                }
            }
        }

        MessageDialog {
            id: computeSubmitErrorDialog

            property string errorType  // Used to specify signals' behavior
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

            property var selectedNodes: null

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
                // Set up discard button text
                standardButton(Dialog.Discard).text = "Continue without Saving"
            }

            onDiscarded: {
                close()
                computeManager.compute(selectedNodes, true)
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

        MessageDialog {
            id: fileModifiedDialog

            canCopy: false
            icon.text: MaterialIcons.warning
            parent: Overlay.overlay
            preset: "Warning"
            title: "File Modified"
            text: "The file has been modified by another instance."
            detailedText: "Do you want to overwrite the file?"

            // Add a reload file button next to the save button
            footer: DialogButtonBox {
                position: DialogButtonBox.Footer
                standardButtons: Dialog.Save | Dialog.Cancel

                Button {
                    text: "Reload File"

                    onClicked: {
                        _reconstruction.loadUrl(_reconstruction.graph.filepath)
                        fileModifiedDialog.close()
                    }
                }
            }

            onAccepted: _reconstruction.save()
            onDiscarded: close()
        }
    }

    // Message dialogs
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

        onRejected: {
            _window.isClosing = false
        }

        onAccepted: {
            // Save current file
            if (saveAction.enabled && _reconstruction.graph.filepath) {
                saveAction.trigger()
                fireCallback()
            }
            // Open "Save As" dialog
            else {
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
            // Call the callback and reset it
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

    MessageDialog {
        id: computingAtExitDialog
        title: "Operation in progress"
        modal: true
        canCopy: false
        Label {
            text: "Please stop any local computation before exiting Meshroom"
        }
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

    AboutDialog {
        id: aboutDialog
    }

    DialogsFactory {
        id: dialogsFactory
    }

    CompatibilityManager {
        id: compatibilityManager
        uigraph: _reconstruction
    }


    // Actions
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
        id: cutAction

        property string tooltip: "Cut Selected Node(s)"
        text: "Cut Node(s)"
        enabled: _reconstruction ? _reconstruction.nodeSelection.hasSelection : false
        onTriggered: {
            graphEditor.copyNodes()
            graphEditor.uigraph.removeSelectedNodes()
        }
    }

    Action {
        id: copyAction

        property string tooltip: "Copy Selected Node(s)" 
        text: "Copy Node(s)"
        enabled: _reconstruction ? _reconstruction.nodeSelection.hasSelection : false
        onTriggered: graphEditor.copyNodes()
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
                initFileDialogFolder(loadTemplateDialog)
                loadTemplateDialog.open()
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

            onClicked: {
                if (!ensureNotComputing())
                    return
                ensureSaved(function() {
                    _reconstruction.clear()
                    if (mainStack.depth == 1)
                        mainStack.replace("Homepage.qml")
                    else
                        mainStack.pop()
                })
            }
        }
        MenuBar {
            palette.window: Qt.darker(activePalette.window, 1.15)
            Menu {
                title: "File"
                Action {
                    id: newAction
                    text: "New"
                    shortcut: "Ctrl+N"
                    onTriggered: ensureSaved(function() {
                        _reconstruction.new()
                    })
                }
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

                            ToolTip {
                                id: toolTip

                                delay: 200
                                text: modelData["path"]
                                visible: hovered
                            }
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
                            // Get current time date
                            var date = _reconstruction.graph.getFileDateVersionFromPath(_reconstruction.graph.filepath)

                            // Check if the file has been modified by another instance
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
                MenuItem {
                    id: imageGalleryVisibilityCB
                    text: "Image Gallery"
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
                    // Should be StandardKey.HelpContents, but for some reason it's not stable
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

                ToolTip.text: !(_reconstruction.computingLocally) ? "Compute" : "Stop Computing"
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

                ToolTip.text: "Submit on Render Farm"
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
        function createDialog(func, message) {
            var dialog = func(_window)
            // Set text afterwards to avoid dialog sizing issues
            dialog.title = message.title
            dialog.text = message.text
            dialog.detailedText = message.detailedText
        }

        function onGraphChanged() {
            // Open CompatibilityManager after file loading if any issue is detected
            if (compatibilityManager.issueCount)
                compatibilityManager.open()
            // Trigger fit to visualize all nodes
            graphEditor.fit()
        }

        function onInfo() { createDialog(dialogsFactory.info, arguments[0]) }
        function onWarning() { createDialog(dialogsFactory.warning, arguments[0]) }
        function onError() { createDialog(dialogsFactory.error, arguments[0]) }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 4

        // "ProgressBar" reflecting status of all the chunks in the graph, in their process order
        NodeChunks {
            id: chunksListView
            height: 6
            Layout.fillWidth: true
            model: _reconstruction ? _reconstruction.sortedDFSChunks : null
            highlightChunks: false
        }

        MSplitView {
            id: topBottomSplit
            Layout.fillHeight: true
            Layout.fillWidth: true

            orientation: Qt.Vertical

            // Setup global tooltip style
            ToolTip.toolTip.background: Rectangle { color: activePalette.base; border.color: activePalette.mid }

            WorkspaceView {
                id: workspaceView
                SplitView.fillHeight: true
                SplitView.preferredHeight: 300
                SplitView.minimumHeight: 80
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

            MSplitView {
                id: bottomContainer
                orientation: Qt.Horizontal
                visible: settingsUILayout.showGraphEditor
                SplitView.preferredHeight: 300
                SplitView.minimumHeight: 80

                TabPanel {
                    id: graphEditorPanel
                    SplitView.fillWidth: true
                    SplitView.minimumWidth: 80

                    padding: 4
                    tabs: ["Graph Editor", "Task Manager", "Script Editor"]

                    headerBar: RowLayout {
                        MaterialToolButton {
                            text: MaterialIcons.sync
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

                                Menu {
                                    title: "Auto Layout Depth"

                                    MenuItem {
                                        id: autoLayoutMinimum
                                        text: "Minimum"
                                        checkable: true
                                        checked: _reconstruction.layout.depthMode === 0
                                        ToolTip.text: "Sets the Auto Layout Depth Mode to use Node's Minimum depth"
                                        ToolTip.visible: hovered
                                        ToolTip.delay: 200
                                        onToggled: {
                                            if (checked) {
                                                _reconstruction.layout.depthMode = 0;
                                                autoLayoutMaximum.checked = false;
                                            }
                                            // Prevents cases where the user unchecks the currently checked option
                                            autoLayoutMinimum.checked = true;
                                        }
                                    }
                                    MenuItem {
                                        id: autoLayoutMaximum
                                        text: "Maximum"
                                        checkable: true
                                        checked: _reconstruction.layout.depthMode === 1
                                        ToolTip.text: "Sets the Auto Layout Depth Mode to use Node's Maximum depth"
                                        ToolTip.visible: hovered
                                        ToolTip.delay: 200
                                        onToggled: {
                                            if (checked) {
                                                _reconstruction.layout.depthMode = 1;
                                                autoLayoutMinimum.checked = false;
                                            }
                                            // Prevents cases where the user unchecks the currently checked option
                                            autoLayoutMaximum.checked = true;
                                        }
                                    }
                                }

                                Menu {
                                    title: "Refresh Nodes Method"

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
                                    }
                                }
                                }
                            }
                        }
                    }

                    GraphEditor {
                        id: graphEditor
                        anchors.fill: parent

                        visible: graphEditorPanel.currentTab === 0

                        uigraph: _reconstruction
                        nodeTypesModel: _nodeTypes

                        onNodeDoubleClicked: function(mouse, node) {
                            _reconstruction.setActiveNode(node);
                            workspaceView.viewNode(node, mouse);
                        }
                        onComputeRequest: function(nodes) {
                            _reconstruction.forceNodesStatusUpdate();
                            computeManager.compute(nodes)
                        }
                        onSubmitRequest: function(nodes) {
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
                        anchors.fill: parent

                        visible: graphEditorPanel.currentTab === 1

                        uigraph: _reconstruction
                        taskManager: _reconstruction ? _reconstruction.taskManager : null
                    }

                    ScriptEditor {
                        id: scriptEditor
                        anchors.fill: parent
                        rootApplication: root

                        visible: graphEditorPanel.currentTab === 2
                    }
                }

                NodeEditor {
                    id: nodeEditor
                    SplitView.preferredWidth: 500
                    SplitView.minimumWidth: 80

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
}