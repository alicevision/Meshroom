import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import MaterialIcons 2.2

/**
 * PluginTaskDelegate renders one row of the task queue.
 */

ItemDelegate {
    id: root

    property var task: null
    property bool current: false

    property int rowSpacing: 8
    property int rowPadding: 8

    // Signals
    signal cancelRequested()

    readonly property string status: task ? task.status : ""

    // Status Color
    readonly property color statusColor: {
        switch (status) {
            case "RUNNING": return palette.highlight
            case "SUCCEEDED": return "#4CAF50"
            case "FAILED": return "#F44336"
            case "CANCELLED": return '#f4A236'
            default: return palette.mid
        }
    }

    // Status Icon
    readonly property string statusIcon: {
        switch (status) {
            case "RUNNING": return MaterialIcons.play_circle_outline
            case "SUCCEEDED": return MaterialIcons.check_circle_outline
            case "FAILED": return MaterialIcons.error_outline
            case "CANCELLED": return MaterialIcons.remove_circle_outline
            default: return MaterialIcons.schedule
        }
    }

    // Status Text
    readonly property string statusText: {
        switch (status) {
            case "PENDING": return "Pending"
            case "RUNNING": return task.cancelRequested ? "Stopping…" : "Running"
            case "SUCCEEDED": return "Done"
            case "FAILED": return task.error || "Failed"
            case "CANCELLED": return "Cancelled"
            default: return ""
        }
    }

    width: ListView.view ? ListView.view.width : implicitWidth
    hoverEnabled: true
    leftPadding: root.rowPadding
    rightPadding: root.rowPadding
    topPadding: root.rowPadding
    bottomPadding: root.rowPadding

    background: Rectangle {
        color: root.current ? palette.window
               : root.hovered ? Qt.lighter(palette.base, 1.150)
               : palette.base

        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: 1
            color: palette.mid
        }
    }

    contentItem: RowLayout {
        spacing: root.rowSpacing

        // Status icon
        Label {
            text: root.statusIcon
            font.family: MaterialIcons.fontFamily
            font.pointSize: 12
            color: root.statusColor
        }

        // Kind
        Label {
            text: root.task.kind + " plugin"
            font.capitalization: Font.Capitalize
            Layout.preferredWidth: implicitWidth
        }

        // Plugin Name
        Label {
            text: root.task.pluginName
            font.bold: true
            elide: Text.ElideRight
            Layout.preferredWidth: implicitWidth
            Layout.maximumWidth: root.width * 0.4
        }

        // Status / Error
        Label {
            text: (root.status === "FAILED" ? root.statusText : root.statusText.toLowerCase() + ".") 
            color: root.status === "FAILED" ? root.statusColor : palette.text
            opacity: 0.6
            elide: Text.ElideRight
            Layout.fillWidth: true

            ToolTip.text: text
            ToolTip.visible: statusHover.hovered && truncated
            HoverHandler { id: statusHover }
        }

        // Cancel Button
        MaterialToolButton {
            visible: !root.task.isFinished
            enabled: !root.task.cancelRequested
            text: MaterialIcons.close
            font.pointSize: 10
            ToolTip.text: root.status === "PENDING" ? "Remove from the queue" : "Interrupt"
            ToolTip.visible: hovered
            onClicked: root.cancelRequested()
        }
    }
}
