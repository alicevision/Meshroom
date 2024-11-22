import QtCore

import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs

import Qt.labs.platform 1.0 as Platform

ApplicationWindow {
    id: _window

    width: settingsGeneral.windowWidth
    height: settingsGeneral.windowHeight
    minimumWidth: 650
    minimumHeight: 500
    visible: true

    property bool isClosing: false

    title: {
        var t = (_reconstruction && _reconstruction.graph && _reconstruction.graph.filepath) ? _reconstruction.graph.filepath : "Untitled"
        if (_reconstruction && !_reconstruction.undoStack.clean)
            t += "*"
        t += " - " + Qt.application.name + " " + Qt.application.version
        return t
    }

    onClosing: function(close) {
        // Make sure document is saved before exiting application
        close.accepted = false
        if (!ensureNotComputing())
            return
        isClosing = true
        ensureSaved(function() { Qt.quit() })
    }

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
    }

    SystemPalette { id: activePalette }
    SystemPalette { id: disabledPalette; colorGroup: SystemPalette.Disabled }

    Settings {
        id: settingsGeneral
        category: "General"
        property int windowWidth: 1280
        property int windowHeight: 720
    }

    Component.onDestruction: {
        // Store main window dimensions in persisting Settings
        settingsGeneral.windowWidth = _window.width
        settingsGeneral.windowHeight = _window.height
    }

    function initFileDialogFolder(dialog, importImages = false) {
        let folder = ""
        let project = ""
        try {
            // The list of recent projects might be empty, hence the try/catch
            project = MeshroomApp.recentProjectFiles[0]["path"]
        } catch (error) {
            console.info("The list of recent projects is currently empty.")
        }
        let currentItem = mainStack.currentItem

        if (currentItem instanceof Homepage) {
            // From the homepage, take the folder from the most recent project (no prior check on its existence)
            if (project != "" && Filepath.exists(project)) {
                folder = Filepath.stringToUrl(Filepath.dirname(project))
            }
        } else {

            if (currentItem.imagesFolder.toString() === "" && currentItem.workspaceView.imageGallery.galleryGrid.itemAtIndex(0) !== null) {
                // Set the initial folder for the "import images" dialog if it hasn't been set already
                currentItem.imagesFolder = Filepath.stringToUrl(Filepath.dirname(currentItem.workspaceView.imageGallery.galleryGrid.itemAtIndex(0).source))
            }

            if (_reconstruction.graph && _reconstruction.graph.filepath) {
                // If the opened project has been saved, the dialog will open in the same folder
                folder = Filepath.stringToUrl(Filepath.dirname(_reconstruction.graph.filepath))
            } else {
                // If the currently opened project has not been saved, the dialog will open in the same
                // folder as the most recent project if it exists; otherwise, it will not be set
                if (project != "" && Filepath.exists(project)) {
                    folder = Filepath.stringToUrl(Filepath.dirname(project))
                }
            }

            // If the dialog that's being opened is the "import images" dialog, use the "imagesFolder" property
            // which contains the last folder used to import images rather than the folder in which
            // projects have been saved
            if (importImages && currentItem.imagesFolder.toString() !== "" && Filepath.exists(imagesFolder)) {
                folder = currentItem.imagesFolder
            }
        }

        dialog.folder = folder
    }

    Platform.FileDialog {
        id: openFileDialog
        options: Platform.FileDialog.DontUseNativeDialog
        title: "Open File"
        nameFilters: ["Meshroom Graphs (*.mg)"]
        onAccepted: {
            if (mainStack.currentItem instanceof Homepage) {
                mainStack.push("Application.qml")
            }
            if (_reconstruction.loadUrl(currentFile)) {
                MeshroomApp.addRecentProjectFile(currentFile.toString())
            }
        }
    }

    // Check if document has been saved
    function ensureSaved(callback)
    {
        var saved = _reconstruction.undoStack.clean
        if (!saved) {  // If current document is modified, open "unsaved dialog"
            mainStack.currentItem.unsavedDialog.prompt(callback)
        } else {  // Otherwise, directly call the callback
            callback()
        }
        return saved
    }

    // Check and return whether no local computation is in progress
    function ensureNotComputing()
    {
        if (_reconstruction.computingLocally) {
            // Open a warning dialog to ask for computation to be stopped
            mainStack.currentItem.computingAtExitDialog.open()
            return false
        }
        return true
    }


    Action {

        shortcut: "Ctrl+Shift+P"
        onTriggered: _PaletteManager.togglePalette()
    }

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
