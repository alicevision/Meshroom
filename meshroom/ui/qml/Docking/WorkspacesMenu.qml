import QtQuick
import QtQuick.Controls

/**
 * WorkspacesMenu lists the workspaces (named layouts of the panels) of a DockLayoutManager to load
 * them, and gives access to saving the current layout as a workspace or deleting one: those are
 * requested through signals, the dialogs being displayed by WorkspaceDialogs.
 */

Menu {
    id: root

    /// The DockLayoutManager holding the layout
    property var layoutModel

    signal saveRequested()
    signal deleteRequested(string name)

    title: "Workspaces"

    MenuItem {
        text: root.layoutModel.defaultWorkspace
        ToolTip.visible: hovered
        ToolTip.delay: 500
        ToolTip.text: "Reset the layout of the panels"
        onTriggered: root.layoutModel.loadWorkspace(text)
    }

    Repeater {
        model: root.layoutModel.workspaceNames
        MenuItem {
            text: modelData
            onTriggered: root.layoutModel.loadWorkspace(modelData)
        }
    }

    MenuSeparator {}

    MenuItem {
        text: "Save Workspace As..."
        onTriggered: root.saveRequested()
    }

    Menu {
        title: "Delete Workspace"
        enabled: root.layoutModel.workspaceNames.length > 0
        Repeater {
            model: root.layoutModel.workspaceNames
            MenuItem {
                text: modelData
                onTriggered: root.deleteRequested(modelData)
            }
        }
    }
}
