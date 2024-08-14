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

    Component.onDestruction: {
        // store main window dimensions in persisting Settings
        settings_General.windowWidth = _window.width
        settings_General.windowHeight = _window.height
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
        options: Platform.FileDialog.DontUseNativeDialog

        signal closed(var result)

        title: "Save File"
        nameFilters: ["Meshroom Graphs (*.mg)"]
        defaultSuffix: ".mg"
        fileMode: Platform.FileDialog.SaveFile
        onAccepted: {
            _reconstruction.saveAs(currentFile)
            closed(Platform.Dialog.Accepted)
            MeshroomApp.addRecentProjectFile(currentFile.toString())
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
            _reconstruction.saveAsTemplate(currentFile)
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

        function compute(nodes, force) {
            if (!force && warnIfUnsaved && !_reconstruction.graph.filepath)
            {
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
                // set up discard button text
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

    Platform.FileDialog {
        id: openFileDialog
        options: Platform.FileDialog.DontUseNativeDialog
        title: "Open File"
        nameFilters: ["Meshroom Graphs (*.mg)"]
        onAccepted: {
            if (_reconstruction.loadUrl(currentFile)) {
                MeshroomApp.addRecentProjectFile(currentFile.toString())
            }
        }
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
        options: FileDialog.DontUseNativeDialog
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
        options: FileDialog.DontUseNativeDialog
        title: "Import Project"
        fileMode: Platform.FileDialog.OpenFile
        nameFilters: ["Meshroom Graphs (*.mg)"]
        onAccepted: {
            graphEditor.uigraph.importProject(currentFile)
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
    Action {
        id: cutAction

        property string tooltip: {
            var s = "Copy selected node"
            s += (_reconstruction && _reconstruction.selectedNodes.count > 1 ? "s (" : " (") + getSelectedNodesName()
            s += ") to the clipboard and remove them from the graph"
            return s
        }
        text: "Cut Node" + (_reconstruction && _reconstruction.selectedNodes.count > 1 ? "s " : " ")
        enabled: _reconstruction ? _reconstruction.selectedNodes.count > 0 : false
        onTriggered: {
            graphEditor.copyNodes()
            graphEditor.uigraph.removeNodes(graphEditor.uigraph.selectedNodes)
        }
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
    }

    Action {
        id: pasteAction

        property string tooltip: "Paste the clipboard content to the project if it contains valid nodes"
        text: "Paste Node(s)"
        onTriggered: graphEditor.pasteNodes()
    }


    

    // TODO: uncomment for Qt6 to re-enable the alternative palette (the alternative palette and the disabled items currently cannot both be supported)
    /* Action {

        shortcut: "Ctrl+Shift+P"
        onTriggered: _PaletteManager.togglePalette()
    } */

    StackView {
        id: mainStack
        anchors.fill: parent

        Component.onCompleted: {
            if (_reconstruction.active) {
                mainStack.push("Application.qml")
            } else {
                mainStack.push("Homepage.qml")
            }
        }

        pushExit: Transition {}
        pushEnter: Transition {}
        popExit: Transition {}
        popEnter: Transition {}
        replaceEnter: Transition {}
        replaceExit: Transition {}
    }

    background: MouseArea {
        onPressed: {
            forceActiveFocus();
        }
    }
 }
