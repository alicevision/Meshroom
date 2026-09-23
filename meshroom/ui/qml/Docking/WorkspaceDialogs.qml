import QtQuick
import QtQuick.Controls

import Controls 1.0

/**
 * WorkspaceDialogs holds the dialogs used to manage the workspaces of a DockLayoutManager: saving the
 * current layout under a name, and confirming the deletion of a workspace.
 */

Item {
    id: root

    /// The DockLayoutManager holding the layout
    property var layoutModel

    /// Ask for a name and save the current layout as a workspace
    function promptSave() {
        workspaceNameField.text = ""
        saveDialog.open()
        workspaceNameField.forceActiveFocus()
    }

    /// Ask for a confirmation and delete a workspace
    function confirmDelete(name) {
        deleteDialog.workspaceName = name
        deleteDialog.open()
    }

    MessageDialog {
        id: saveDialog

        readonly property string workspaceName: workspaceNameField.text.trim()
        readonly property bool isDefault: workspaceName.toLowerCase() === root.layoutModel.defaultWorkspace.toLowerCase()

        parent: Overlay.overlay
        title: "Save Workspace"
        preset: "Info"
        canCopy: false
        text: "Save the current layout of the panels as a workspace, to restore it from the View > Workspaces menu."
        helperText: {
            if (isDefault)
                return "This name is reserved to the default layout."
            if (workspaceName && root.layoutModel.hasWorkspace(workspaceName))
                return "A workspace with this name already exists, it will be replaced."
            return ""
        }
        standardButtons: Dialog.Save | Dialog.Cancel

        Component.onCompleted: standardButton(Dialog.Save).enabled = Qt.binding(function() { return saveDialog.workspaceName !== "" && !saveDialog.isDefault })

        TextField {
            id: workspaceNameField
            implicitWidth: 300
            placeholderText: "Workspace name"
            onAccepted: {
                if (saveDialog.standardButton(Dialog.Save).enabled)
                    saveDialog.accept()
            }
        }

        onAccepted: root.layoutModel.saveWorkspace(workspaceName)
    }

    MessageDialog {
        id: deleteDialog

        property string workspaceName

        parent: Overlay.overlay
        title: "Delete Workspace"
        preset: "Warning"
        canCopy: false
        text: "Delete the workspace \"" + workspaceName + "\"?"
        helperText: "This cannot be undone."
        standardButtons: Dialog.Yes | Dialog.Cancel

        onAccepted: root.layoutModel.deleteWorkspace(workspaceName)
    }
}
