import QtQuick
import QtQuick.Controls
import QtQuick.Window

import Controls 1.0

import "Details"
import "List"
import "Tasks"


/**
 * PluginManagerWindow is the top-level window of the plugin manager.
 *
 * It is split into a plugin list next to the details of the selected plugin,
 * and, below, the queue of install / update / remove tasks.
 *
 * The task pane and the plugin actions are only available when local plugins are enabled.
 *
 * The window is application-modal, so that no project can be modified while plugins are managed.
 * A plugin task is only run once the current project is saved, and the window cannot be closed
 * while tasks are in progress.
 */

Window {
    id: root
    title: "Plugin Manager"
    width: 1024
    height: 600
    minimumWidth: 800
    minimumHeight: 600
    color: palette.window
    modality: Qt.ApplicationModal

    onClosing: function(close) {
        if (_pluginTaskQueue.busy) {
            close.accepted = false
            tasksInProgressDialog.open()
        }
    }

    // Handle Current Meshroom Scene State
    function requestTask(addTask) {
        if (_currentScene && _currentScene.computingLocally) {
            computingDialog.open()
            return
        }
        if (_currentScene && !_currentScene.undoStack.clean) {
            unsavedDialog.open()
            return
        }
        addTask()
    }

    // Unsaved Project Dialog
    MessageDialog {
        id: unsavedDialog
        title: "Unsaved Project"
        preset: "Warning"
        canCopy: false
        text: "The current project has unsaved modifications."
        helperText: "Please save the project before installing, updating or removing plugins."
    }

    // Computation in Progress Dialog
    MessageDialog {
        id: computingDialog
        title: "Computation in Progress"
        preset: "Warning"
        canCopy: false
        text: "A local computation is in progress."
        helperText: "Please stop the local computation before installing, updating or removing plugins."
    }

    // Tasks in Progress Dialog
    MessageDialog {
        id: tasksInProgressDialog
        title: "Tasks in Progress"
        preset: "Info"
        canCopy: false
        text: "Plugin tasks are still in progress."
        helperText: "Please wait for them to finish, or cancel them, before closing the Plugin Manager."
    }

    Loader {
        anchors.fill: parent
        active: root.visible
        sourceComponent: MSplitView {
            id: content
            orientation: Qt.Vertical

            MSplitView {
                id: pluginsSplitView
                orientation: Qt.Horizontal
                SplitView.fillWidth: true
                SplitView.preferredHeight: content.height * 0.7
                SplitView.minimumHeight: content.height * 0.5

                // Plugin List
                PluginListPane {
                    id: pluginsListPane
                    SplitView.preferredWidth: content.width * 0.7
                    SplitView.minimumWidth: content.width * 0.5
                }

                // Plugin Details
                PluginDetailsPane {
                    id: pluginDetails
                    plugin: pluginsListPane.currentPlugin
                    SplitView.fillWidth: true
                    SplitView.minimumWidth: content.width * 0.3

                    actionsEnabled: _pluginManager.localPluginsEnabled
                    onInstallRequested: root.requestTask(() => _pluginTaskQueue.install(plugin))
                    onUpdateRequested: root.requestTask(() => _pluginTaskQueue.update(plugin.name))
                    onRemoveRequested: root.requestTask(() => _pluginTaskQueue.remove(plugin.name))
                }
            }

            // Tasks
            Loader {
                id: bottomPaneLoader
                active: _pluginManager.localPluginsEnabled
                visible: active
                SplitView.fillWidth: true
                SplitView.preferredHeight: content.height * 0.3
                SplitView.minimumHeight: content.height * 0.2

                sourceComponent: PluginTaskPane {
                    id: bottomPane
                    tasks: _pluginTaskQueue.tasks
                    runningTask: _pluginTaskQueue.runningTask
                    onCancelRequested: (task) => _pluginTaskQueue.cancel(task)
                    onClearFinishedRequested: _pluginTaskQueue.clearFinished()
                }
            }
        }
    }
}
