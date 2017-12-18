import QtQuick 2.7
import QtQuick.Controls 2.3
import QtQuick.Controls 1.4 as Controls1 // For SplitView
import QtQuick.Layouts 1.1
import QtQuick.Window 2.3
import QtQml.Models 2.2
import Qt.labs.platform 1.0 as Platform
import GraphEditor 1.0
import MaterialIcons 2.2

ApplicationWindow {
    id: _window

    width: 1280
    height: 720
    visible: true
    title: (_reconstruction.graph.filepath ? _reconstruction.graph.filepath : "Untitled") + (_reconstruction.undoStack.clean ? "" : "*") + " - Meshroom"
    font.pointSize: 9

    property variant node: null
    onClosing: {
        // make sure document is saved before exiting application
        close.accepted = false
        if(!ensureNotComputing())
            return
        ensureSaved(function(){ Qt.quit() })
    }

    SystemPalette { id: palette }
    SystemPalette { id: disabledPalette; colorGroup: SystemPalette.Disabled}


    Dialog {
        id: unsavedDialog

        property var _callback: undefined

        title: "Unsaved Document"
        modal: true
        x: parent.width/2 - width/2
        y: parent.height/2 - height/2
        standardButtons: Dialog.Save | Dialog.Cancel | Dialog.Discard
        padding: 15
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

    Dialog {
        id: computingAtExitDialog
        title: "Operation in progress"
        x: parent.width/2 - width/2
        y: parent.height/2 - height/2
        padding: 15
        standardButtons: Dialog.Ok
        modal: true
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

    Dialog {
        // Popup displayed while the application
        // is busy building intrinsics while importing images
        id: buildingIntrinsicsDialog
        modal: true
        x: _window.width / 2 - width/2
        y: _window.height / 2 - height/2
        visible: _reconstruction.buildingIntrinsics
        closePolicy: Popup.NoAutoClose
        title: "Import Images"
        padding: 15

        ColumnLayout {
            anchors.fill: parent
            Label {
                text: "Extracting images metadata... "
                horizontalAlignment: Text.AlignHCenter

                Layout.fillWidth: true
            }
            ProgressBar {
                indeterminate: true
                Layout.fillWidth: true
            }
        }
    }

    Action {
        id: undoAction

        property string tooltip: 'Undo "' +_reconstruction.undoStack.undoText +'"'
        text: "Undo"
        shortcut: "Ctrl+Z"
        enabled: _reconstruction.undoStack.canUndo && !_reconstruction.computing
        onTriggered: _reconstruction.undoStack.undo()
    }
    Action {
        id: redoAction

        property string tooltip: 'Redo "' +_reconstruction.undoStack.redoText +'"'
        text: "Redo"
        shortcut: "Ctrl+Shift+Z"
        enabled: _reconstruction.undoStack.canRedo && !_reconstruction.computing
        onTriggered: _reconstruction.undoStack.redo()
    }

    Action {
        shortcut: "Ctrl+Shift+P"
        onTriggered: _PaletteManager.togglePalette()
    }

    header: MenuBar {
        palette.window: Qt.darker(palette.window, 1.15)
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
                enabled: _reconstruction.graph.filepath != "" && !_reconstruction.undoStack.clean
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
        Menu {
            title: "View"
            Action {
                text: "Fullscreen"
                checkable: true
                checked: _window.visibility == ApplicationWindow.FullScreen
                shortcut: "Ctrl+F"
                onTriggered: _window.visibility == ApplicationWindow.FullScreen ? _window.showNormal() : showFullScreen()
            }
        }
    }

    Controls1.SplitView {
        anchors.fill: parent
        orientation: Qt.Vertical

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.topMargin: 2
            implicitHeight: Math.round(parent.height * 0.7)
            spacing: 4
            Row {
                enabled: !_reconstruction.computingExternally
                anchors.horizontalCenter: parent.horizontalCenter

                Button {
                    property color buttonColor: Qt.darker("#4CAF50", 1.8)
                    text: "▶  Start"
                    palette.button: enabled ? buttonColor : disabledPalette.button
                    palette.window: enabled ? buttonColor : disabledPalette.window
                    palette.buttonText: enabled ? "white" : disabledPalette.buttonText
                    enabled: _reconstruction.viewpoints.count > 2 && !_reconstruction.computing
                    onClicked: _reconstruction.execute(null)
                }
                Button {
                    text: "Stop"
                    enabled: _reconstruction.computingLocally
                    onClicked: _reconstruction.stopExecution()
                }
                Item { width: 20; height: 1 }
                Button {
                    enabled: _reconstruction.viewpoints.count > 2 && !_reconstruction.computing  && _reconstruction.graph.filepath != ""
                    text: "Submit"
                    onClicked: _reconstruction.submit(null)
                }
            }
            Label {
                text: "Graph is being computed externally"
                font.italic: true
                anchors.horizontalCenter: parent.horizontalCenter
                visible: _reconstruction.computingExternally
            }

            // "ProgressBar" reflecting status of all the chunks in the graph, in their process order
            ListView {
                id: chunksListView
                Layout.fillWidth: true
                height: 6
                model: _reconstruction.sortedDFSNodes
                orientation: ListView.Horizontal
                interactive: false

                delegate: NodeChunks {
                    model: object.chunks
                    height: 6
                    chunkWidth: chunksListView.width / _reconstruction.chunksCount
                    width: childrenRect.width
                }
            }

            WorkspaceView {
                id: imageGallery
                reconstruction: _reconstruction
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumHeight: 50
            }
        }
        Panel {
            Layout.fillWidth: true
            Layout.fillHeight: false
            height: Math.round(parent.height * 0.3)
            title: "Graph Editor"

            Controls1.SplitView {
                orientation: Qt.Horizontal
                anchors.fill: parent

                ColumnLayout {
                    Layout.fillHeight: true
                    Layout.fillWidth: true
                    Layout.margins: 10
                    GraphEditor {
                        id: graphEditor
                        Layout.fillHeight: true
                        Layout.fillWidth: true
                        uigraph: _reconstruction
                        nodeTypesModel: _nodeTypes
                        readOnly: _reconstruction.computing
                    }

                }
                Item {
                    implicitHeight: Math.round(parent.height * 0.2)
                    implicitWidth: Math.round(parent.width * 0.3)

                    Loader {
                        anchors.fill: parent
                        anchors.margins: 2
                        active: graphEditor.selectedNode != null
                        sourceComponent: Component {
                            AttributeEditor {
                                node: graphEditor.selectedNode
                                // Make AttributeEditor readOnly when computing
                                readOnly: _reconstruction.computing
                            }
                        }
                    }
                }
            }
        }
    }
 }
