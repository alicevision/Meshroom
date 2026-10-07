import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Controls 1.0
import MaterialIcons 2.2

/**
 * PluginTaskPane displays the queue of plugin tasks, and, at the bottom,
 * the task being run.
 */

Panel {
    id: root

    property var tasks: null        // The tasks of the queue.
    property var runningTask: null  // The task being run, if any.

    // Signals
    signal cancelRequested(var task)
    signal clearFinishedRequested()

    title: "Tasks"
    background: Rectangle { color: palette.base }

    // Header Clear Button
    headerBar: MaterialToolButton {
        text: MaterialIcons.clear_all
        ToolTip.text: "Clear finished tasks"
        ToolTip.visible: hovered
        enabled: listView.count > 0
        onClicked: root.clearFinishedRequested()
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // Task queue
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            ListView {
                id: listView
                anchors.fill: parent
                clip: true
                model: root.tasks

                delegate: PluginTaskDelegate {
                    task: model.object
                    current: root.runningTask !== null && root.runningTask === model.object
                    onCancelRequested: root.cancelRequested(model.object)
                }
            }

            // Placeholder
            Label {
                anchors.centerIn: parent
                visible: listView.count === 0
                text: "No tasks"
                opacity: 0.6
            }
        }

        // Separator
        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: palette.mid
        }

        // Current task
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: currentTaskLayout.implicitHeight + 2 * currentTaskLayout.anchors.margins
            color: Qt.darker(palette.base, 1.4)

            RowLayout {
                id: currentTaskLayout
                anchors.fill: parent
                anchors.margins: 16
                spacing: 12

                // Name + current step
                ColumnLayout {
                    spacing: 8
                    Layout.preferredWidth: parent.width * 0.35

                    RowLayout {
                        spacing: 4
                        Layout.fillWidth: true

                        // Task Label
                        Label {
                            text: root.runningTask ? root.runningTask.kind + " plugin" : "No task running"
                            font.capitalization: root.runningTask ? Font.Capitalize : Font.MixedCase
                            font.bold: root.runningTask
                            opacity: root.runningTask ? 1 : 0.5
                        }

                        // Plugin Name
                        Label {
                            text: root.runningTask ? root.runningTask.pluginName : ""
                            visible: root.runningTask
                            font.bold: true
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                    }

                    RowLayout {
                        spacing: 10
                        visible: root.runningTask
                        Layout.fillWidth: true

                        BusyIndicator {
                            padding: 0
                            running: root.runningTask !== null
                            Layout.preferredWidth: 10
                            Layout.preferredHeight: 10
                            opacity: 0.7
                        }

                        // Task Message
                        Label {
                            text: root.runningTask ? root.runningTask.message : ""
                            elide: Text.ElideRight
                            opacity: 0.7
                            Layout.fillWidth: true
                        }
                    }
                }

                // Progress
                ProgressBar {
                    id: progressBar
                    // No progress reported yet: show a chase animation
                    indeterminate: root.runningTask !== null && root.runningTask.progress === 0
                    from: 0
                    to: 1
                    value: root.runningTask ? root.runningTask.progress : 0
                    Layout.fillWidth: true
                    Layout.minimumWidth: 200
                }

                // Progress Percentage
                Label {
                    opacity: root.runningTask ? progressBar.indeterminate ? 0 : 1 : 0.5
                    text: Math.round((root.runningTask ? root.runningTask.progress : 0) * 100) + "%"
                    horizontalAlignment: Text.AlignRight
                    Layout.preferredWidth: 36
                }

                // Interrupt
                MaterialToolButton {
                    enabled: root.runningTask ? !root.runningTask.cancelRequested : false
                    text: MaterialIcons.stop_circle
                    ToolTip.text: enabled ? "Interrupt" : "Stopping…"
                    ToolTip.visible: hovered && root.runningTask !== null
                    onClicked: root.cancelRequested(root.runningTask)
                }
            }
        }
    }
}
