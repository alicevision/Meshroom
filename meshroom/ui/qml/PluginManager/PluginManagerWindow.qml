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
 */

Window {
    id: root
    title: "Plugin Manager"
    width: 1024
    height: 600
    minimumWidth: 800
    minimumHeight: 600
    color: palette.window

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
                    onInstallRequested: _pluginTaskQueue.install(plugin)
                    onUpdateRequested: _pluginTaskQueue.update(plugin.name)
                    onRemoveRequested: _pluginTaskQueue.remove(plugin.name)
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
