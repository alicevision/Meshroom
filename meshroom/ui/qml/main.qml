import QtQuick 2.7
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.1
import QtQuick.Window 2.3
import QtQml.Models 2.2
import Qt.labs.platform 1.0 as Platform

ApplicationWindow {
    id: _window

    width: 1280
    height: 720
    visible: true
    title: (_reconstruction.filepath ? _reconstruction.filepath : "Untitled") + (_reconstruction.undoStack.clean ? "" : "*") + " - Meshroom"
    font.pointSize: 10

    property variant node: null

    onClosing: {
        // make sure document is saved before exiting application
        close.accepted = false
        ensureSaved(function(){ Qt.quit() })
    }

    Dialog {
        id: unsavedDialog

        property var _callback: undefined

        title: "Unsaved Document"
        modal: true
        x: parent.width/2 - width/2
        y: parent.height/2 - height/2
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

        Label {
            text: "Your current Graph is not saved"
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
        }
        onRejected: closed(Platform.Dialog.Rejected)
    }

    Platform.FileDialog {
        id: openFileDialog
        title: "Open File"
        nameFilters: ["Meshroom Graphs (*.mg)"]
        onAccepted: {
            _reconstruction.loadUrl(file.toString())
            graphEditor.doAutoLayout()
        }
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

    Action {
        id: undoAction

        property string tooltip: 'Undo "' +_reconstruction.undoStack.undoText +'"'
        text: "Undo"
        shortcut: "Ctrl+Z"
        enabled: _reconstruction.undoStack.canUndo
        onTriggered: _reconstruction.undoStack.undo()
    }
    Action {
        id: redoAction

        property string tooltip: 'Redo "' +_reconstruction.undoStack.redoText +'"'
        text: "Redo"
        shortcut: "Ctrl+Shift+Z"
        enabled: _reconstruction.undoStack.canRedo
        onTriggered: _reconstruction.undoStack.redo()
    }

    header: MenuBar {
        Menu {
            title: "File"
            Action {
                text: "New"
                onTriggered: ensureSaved(function() { _reconstruction.new(); graphEditor.doAutoLayout() })
            }
            Action {
                text: "Open"
                shortcut: "Ctrl+O"
                onTriggered: ensureSaved(function() { openFileDialog.open() })
            }
            Action {
                id: saveAction
                text: "Save"
                shortcut: "Ctrl+S"
                enabled: _reconstruction.filepath != "" && !_reconstruction.undoStack.clean
                onTriggered: _reconstruction.save()
            }
            Action {
                id: saveAsAction
                text: "Save As..."
                shortcut: "Ctrl+Shift+S"
                onTriggered: saveFileDialog.open()
            }
            MenuSeparator { }
            Action {
                text: "Quit"
                onTriggered: Qt.quit()
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
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 4
        Row {
            spacing: 1
            Layout.fillWidth: true

            Button {
                text: "Execute"
                enabled: _reconstruction.graph.nodes.count && !_reconstruction.computing
                onClicked: _reconstruction.execute(null)
            }
            Button {
                text: "Stop"
                enabled: _reconstruction.computing
                onClicked: _reconstruction.stopExecution()
            }
        }
        GraphEditor {
            id: graphEditor
            graph: _reconstruction.graph
            Layout.fillWidth: true
            Layout.preferredHeight: parent.height * 0.3
            Layout.margins: 10
        }

        Loader {
            Layout.fillWidth: true
            Layout.fillHeight: true
            active: graphEditor.selectedNode != null
            sourceComponent: Component {
                AttributeEditor {
                    node: graphEditor.selectedNode
                    // Disable editor when computing
                    enabled: !_reconstruction.computing
                }
            }
        }
    }
 }



