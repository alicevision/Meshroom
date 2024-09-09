import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Window 2.15
import QtQuick.Dialogs 1.3

import Qt.labs.platform 1.0 as Platform
import Qt.labs.settings 1.0

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

    onClosing: {
        // Make sure document is saved before exiting application
        close.accepted = false
        if (!ensureNotComputing())
            return
        isClosing = true
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

    Settings {
        id: settingsGeneral
        category: 'General'
        property int windowWidth: 1280
        property int windowHeight: 720
    }

    Component.onDestruction: {
        // Store main window dimensions in persisting Settings
        settingsGeneral.windowWidth = _window.width
        settingsGeneral.windowHeight = _window.height
    }

    function initFileDialogFolder(dialog, importImages = false) {
        let folder = "";

        if (mainStack.currentItem instanceof Homepage) {
            folder = Filepath.stringToUrl(Filepath.dirname(MeshroomApp.recentProjectFiles[0]["path"]))
        } else {
            if (mainStack.currentItem.imagesFolder.toString() === "" && mainStack.currentItem.workspaceView.imageGallery.galleryGrid.itemAtIndex(0) !== null) {
                imagesFolder = Filepath.stringToUrl(Filepath.dirname(mainStack.currentItem.workspaceView.imageGallery.galleryGrid.itemAtIndex(0).source))
            }

            if (_reconstruction.graph && _reconstruction.graph.filepath) {
                folder = Filepath.stringToUrl(Filepath.dirname(_reconstruction.graph.filepath))
            } else {
                var projects = MeshroomApp.recentProjectFiles

                if (projects.length > 0 && Filepath.exists(projects[0]["path"])) {
                    folder = Filepath.stringToUrl(Filepath.dirname(projects[0]["path"]))
                }
            }

            if (importImages && mainStack.currentItem.imagesFolder.toString() !== "" && Filepath.exists(imagesFolder)) {
                folder = mainStack.currentItem.imagesFolder
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
            if (_reconstruction.loadUrl(currentFile)) {
                MeshroomApp.addRecentProjectFile(currentFile.toString())
            }
            if (mainStack.currentItem instanceof Homepage) {
                mainStack.push("Application.qml")
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
        if (_reconstruction.computingLocally)
        {
            // Open a warning dialog to ask for computation to be stopped
            mainStack.currentItem.computingAtExitDialog.open()
            return false
        }
        return true
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
