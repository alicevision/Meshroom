import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import MaterialIcons 2.2
import Utils 1.0
import DataObjects 1.0

/**
 * Text file viewer with auto-reload feature.
 * Uses a ListView with one delegate by line instead of a TextArea for performance reasons.
 */

Item {
    id: root

    /// Source text file to load
    property url source
    /// Whether to periodically reload the source file
    property bool autoReload: false
    /// Interval (in ms) at which source file should be reloaded if autoReload is enabled
    property int autoReloadInterval: 2000
    /// Whether the source is currently being loaded
    property bool loading: false
    /// Whether a large file warning is being displayed (file > 500 MB)
    property bool largeFileWarning: false
    /// File size in MB when a large file warning is displayed
    property real largeFileSizeMB: 0
    /// Human-readable file size string for the large file warning
    readonly property string largeFileSizeStr: Format.GB2SizeStr(largeFileSizeMB / 1024)
    /// Whether the user confirmed loading the current large source file
    property bool confirmLargeLoad: false

    onSourceChanged: {
        confirmLargeLoad = false
        loadSource()
    }
    onAutoReloadChanged: loadSource()
    onVisibleChanged: if (visible) loadSource()

    RowLayout {
        anchors.fill: parent
        spacing: 0

        // Toolbar
        Pane {
            Layout.alignment: Qt.AlignTop
            Layout.fillHeight: true
            padding: 0
            background: Rectangle { color: Qt.darker(Colors.sysPalette.window, 1.2) }
            Column {
                height: parent.height
                spacing: 1
                MaterialToolButton {
                    text: MaterialIcons.refresh
                    ToolTip.text: "Reload"
                    onClicked: loadSource()
                }
                MaterialToolButton {
                    text: MaterialIcons.vertical_align_top
                    ToolTip.text: "Scroll to Top"
                    onClicked: textView.positionViewAtBeginning()
                }
                MaterialToolButton {
                    id: autoscroll
                    text: MaterialIcons.vertical_align_bottom
                    ToolTip.text: "Scroll to Bottom"
                    onClicked: textView.positionViewAtEnd()
                    checkable: false
                    checked: textView.atYEnd
                }
                MaterialToolButton {
                    text: MaterialIcons.assignment
                    ToolTip.text: "Copy"
                    onClicked: copySubMenu.open()
                    Menu {
                        id: copySubMenu
                        x: parent.width

                        MenuItem {
                            text: "Copy Visible Text"
                            onTriggered: {
                                var t = ""
                                for (var i = textView.firstVisibleIndex(); i < textView.lastVisibleIndex(); ++i)
                                    t += textView.model.get(i).line + "\n"
                                Clipboard.setText(t)
                            }
                        }
                        MenuItem {
                            text: "Copy All"
                            onTriggered: {
                                Clipboard.setText(textView.text)
                            }
                         }
                    }
                }
                MaterialToolButton {
                    text: MaterialIcons.open_in_new
                    ToolTip.text: "Open Externally"
                    enabled: root.source !== ""
                    onClicked: Qt.openUrlExternally(root.source)
                }
            }
        }

        MouseArea {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.margins: 4

            ListView {
                id: textView

                property string text

                LogLinesModel {
                    id: logLinesModel
                }

                onTextChanged: {
                    logLinesModel.setText(text);
                }

                model: logLinesModel
                visible: text != ""

                anchors.fill: parent
                clip: true
                focus: true

                // Custom key navigation handling
                keyNavigationEnabled: false
                highlightFollowsCurrentItem: true
                highlightMoveDuration: 0
                Keys.onPressed: function(event) {
                    switch (event.key) {
                        case Qt.Key_Home:
                            textView.positionViewAtBeginning()
                            break
                        case Qt.Key_End:
                            textView.positionViewAtEnd()
                            break
                        case Qt.Key_Up:
                            currentIndex = firstVisibleIndex()
                            decrementCurrentIndex()
                            break;
                        case Qt.Key_Down:
                            currentIndex = lastVisibleIndex()
                            incrementCurrentIndex()
                            break;
                        case Qt.Key_PageUp:
                            textView.positionViewAtIndex(firstVisibleIndex(), ListView.End)
                            break
                        case Qt.Key_PageDown:
                            textView.positionViewAtIndex(lastVisibleIndex(), ListView.Beginning)
                            break
                    }
                }

                function setText(value) {
                    // Store current first index
                    var topIndex = firstVisibleIndex()
                    // Store whether autoscroll to bottom is active
                    var scrollToBottom = atYEnd && autoscroll.checked
                    // Replace text
                    text = value

                    // Restore content position by either:
                    //  - autoscrolling to bottom
                    if (scrollToBottom)
                        positionViewAtEnd()
                    //  - setting first visible index back (when possible)
                    else if (topIndex !== firstVisibleIndex())
                        positionViewAtIndex(Math.min(topIndex, count - 1), ListView.Beginning)
                }

                function firstVisibleIndex() {
                    return indexAt(contentX, contentY)
                }

                function lastVisibleIndex() {
                    return indexAt(contentX, contentY + height - 2)
                }

                ScrollBar.vertical: MScrollBar { id: vScrollBar }

                ScrollBar.horizontal: MScrollBar {}

                // TextMetrics for line numbers column
                TextMetrics {
                    id: lineMetrics
                    font.family: "Monospace, Consolas, Monaco"
                    text: textView.count * 10
                }

                // TextMetrics for textual progress bar
                TextMetrics {
                    id: progressMetrics
                    // Total number of character in textual progress bar
                    property int count: 51
                    property string character: '*'
                    text: character.repeat(count)
                }

                delegate: RowLayout {
                    width: textView.width
                    spacing: 6

                    property var logLine: {
                        var entry = textView.model.get(index)
                        if (entry)
                        {
                            return entry
                        }
                        
                        return { "line": "", "duration": -1, "time": "00:00:00", "level": LogLevelEnum.INFO }
                    }

                    Item {
                        Layout.minimumWidth: childrenRect.width
                        Layout.fillHeight: true
                        RowLayout {
                            height: parent.height
                            // Colored marker to quickly indicate duration
                            Rectangle {
                                width: 4
                                Layout.fillHeight: true
                                color: Colors.durationColor(logLine.duration)
                            }
                            // Line number
                            Label {
                                text: index + 1
                                Layout.minimumWidth: lineMetrics.width
                                rightPadding: 6
                                Layout.fillHeight: true
                                horizontalAlignment: Text.AlignRight
                                color: "#CCCCCC"
                            }
                        }
                        // Display a tooltip with the duration when hovered
                        MouseArea {
                            id: mouseArea
                            hoverEnabled: true
                            anchors.fill: parent
                        }
                        enabled: logLine.duration > 0
                        ToolTip.text: "Elapsed time: " + Format.sec2timeStr(logLine.duration) + "\nTime: " + (logLine.duration >= 0 ? logLine.time : "Unknown")
                        ToolTip.visible: mouseArea.containsMouse && logLine.duration >= 0
                    }

                    Loader {
                        id: delegateLoader
                        Layout.fillWidth: true
                        // Default line delegate
                        sourceComponent: line_component

                        // Line delegate selector based on content
                        StateGroup {
                            states: [
                                State {
                                    name: "progressBar"
                                    // Detect textual progressbar (non-empty line with only progressbar character)
                                    when: logLine.line.trim().length
                                          && logLine.line.split(progressMetrics.character).length - 1 === logLine.line.trim().length
                                    PropertyChanges {
                                        target: delegateLoader
                                        sourceComponent: progressBar_component
                                    }
                                }
                            ]
                        }

                        // ProgressBar delegate
                        Component {
                            id: progressBar_component
                            Item {
                                Layout.fillWidth: true
                                implicitHeight: progressMetrics.height
                                ProgressBar {
                                    width: progressMetrics.width
                                    height: parent.height - 2
                                    anchors.verticalCenter: parent.verticalCenter
                                    from: 0
                                    to: progressMetrics.count
                                    value: logLine.line.length
                                }
                            }
                        }

                        // Default line delegate
                        Component {
                            id: line_component
                            TextInput {
                                wrapMode: Text.WrapAnywhere
                                text: logLine.line
                                font.family: "Monospace, Consolas, Monaco"
                                padding: 0
                                selectByMouse: true
                                readOnly: true
                                selectionColor: Colors.sysPalette.highlight
                                persistentSelection: false
                                Keys.forwardTo: [textView]

                                color: {
                                    // Color line according to log level
                                    switch (logLine.level)
                                    {
                                    case LogLevelEnum.TRACE:
                                        return Qt.darker(palette.text, 2)
                                    case LogLevelEnum.DEBUG:
                                        return Qt.darker(palette.text, 1.5)
                                    case LogLevelEnum.WARNING:
                                        return Colors.orange
                                    case LogLevelEnum.ERROR:
                                        return Colors.red
                                    case LogLevelEnum.FATAL:
                                    case LogLevelEnum.CRITICAL:
                                        return Colors.firebrick
                                    default:
                                        return palette.text
                                    }
                                }
                            }
                        }
                    }
                }
            }

            RowLayout {
                anchors.fill: parent
                anchors.rightMargin: vScrollBar.width
                z: -1

                Item {
                    Layout.preferredWidth: lineMetrics.width
                    Layout.fillHeight: true
                }

                // IBeamCursor shape overlay
                MouseArea {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    cursorShape: Qt.IBeamCursor
                }
            }

            // File loading indicator
            BusyIndicator {
                Component.onCompleted: running = Qt.binding(function() { return root.loading })
                padding: 0
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                implicitWidth: 16
                implicitHeight: 16
            }

            // Large file warning overlay
            ColumnLayout {
                visible: root.largeFileWarning
                anchors.centerIn: parent
                spacing: 8

                Label {
                    Layout.alignment: Qt.AlignHCenter
                    font.family: MaterialIcons.fontFamily
                    font.pointSize: 24
                    text: MaterialIcons.warning
                    color: Colors.orange
                }
                Label {
                    Layout.alignment: Qt.AlignHCenter
                    font.bold: true
                    text: "File size exceeds 500 MB"
                }
                Label {
                    Layout.alignment: Qt.AlignHCenter
                    text: "File size: " + root.largeFileSizeStr
                }
                Label {
                    Layout.alignment: Qt.AlignHCenter
                    text: "Loading this file may take a while and freeze the interface."
                }
                Button {
                    Layout.alignment: Qt.AlignHCenter
                    text: "Load File (" + root.largeFileSizeStr + ")"
                    onClicked: {
                        root.confirmLargeLoad = true
                        root.largeFileWarning = false
                        root._performLoad()
                    }
                }
            }
        }
    }

    // Auto-reload current file timer
    Timer {
        id: reloadTimer
        running: root.autoReload
        interval: root.autoReloadInterval
        repeat: false // timer is restarted in request's callback (see loadSource)
        onTriggered: loadSource()
    }


    // Load current source file and update ListView's model
    function loadSource() {
        if (!visible)
            return

        // Check file size before loading (unless user already confirmed for this source)
        if (!confirmLargeLoad) {
            var fSizeMB = Filepath.fileSizeMB(root.source)
            if (fSizeMB > 500) {
                textView.setText("")
                largeFileSizeMB = fSizeMB
                largeFileWarning = true
                return
            }
        }

        largeFileWarning = false
        _performLoad()
    }

    // Internal function that performs the actual XHR file load, bypassing the size check
    function _performLoad() {
        loading = true
        var xhr = new XMLHttpRequest

        xhr.open("GET", root.source)
        xhr.onreadystatechange = function() {
            // - cannot rely on 'Last-Modified' header response to verify
            //   that file has changed on disk (not always up-to-date)
            // - instead, let QML engine evaluate whether 'text' property value has changed
            if (xhr.readyState === XMLHttpRequest.DONE) {
                textView.setText(xhr.status === 200 ? xhr.responseText : "")
                loading = false
                // Re-trigger reload source file
                if (autoReload)
                    reloadTimer.restart()
            }
        }
        xhr.send()
    }
}
