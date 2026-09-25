import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

import Controls 1.0
import MaterialIcons 2.2

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
 *
 * The changes made by the tasks only apply after a restart.
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
        // Keep the manager open, as closing it would unlock the application, while:
        // - plugin tasks are still in progress
        // - a restart is required to apply the plugin changes

        if (_pluginTaskQueue.busy) {
            close.accepted = false
            tasksInProgressDialog.open()
        }
        else if (_pluginTaskQueue.restartRequired) {
            close.accepted = false
            restartDialog.open()
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

    // Restart Dialog
    MessageDialog {
        id: restartDialog
        title: "Restart Required"
        preset: "Info"
        canCopy: false
        text: "Plugins have been changed."
        helperText: "Restart Meshroom to apply the changes. The current project will be reopened."
    }

    // Layout
    Loader {
        anchors.fill: parent
        active: root.visible
        sourceComponent: ColumnLayout {
            spacing: 0

            // Restart Banner
            Pane {
                Layout.fillWidth: true
                visible: _pluginTaskQueue.restartRequired
                padding: 12
                background: Rectangle { color: Qt.darker(palette.highlight, 1.7) }

                RowLayout {
                    anchors.fill: parent
                    spacing: 8

                    // Restart Icon
                    Label {
                        text: MaterialIcons.restart_alt
                        font.family: MaterialIcons.fontFamily
                        font.pointSize: 13
                        color: "white"
                    }

                    // Restart Label
                    Label {
                        text: "Restart Meshroom to apply the plugin changes."
                        Layout.fillWidth: true
                        elide: Text.ElideRight
                        color: "white"
                    }

                    // Restart Button
                    Button {
                        text: "Restart Now"
                        enabled: !_pluginTaskQueue.busy
                        onClicked: MeshroomApp.restart()
                    }
                }
            }

            // Plugins
            MSplitView {
                id: content
                Layout.fillWidth: true
                Layout.fillHeight: true
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
}
