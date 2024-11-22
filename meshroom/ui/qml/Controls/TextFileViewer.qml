import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import MaterialIcons 2.2
import Utils 1.0

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

    onSourceChanged: loadSource()
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

                ListModel {
                    id: logLinesModel
                }

                onTextChanged: {
                    updateLogLinesModel(logLinesModel, text);
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
                Keys.onPressed: {
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

                    property var logLine: textView.model.get(index) ? textView.model.get(index) : {"line": "", "duration": -1}

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
                        ToolTip.text: "Elapsed time: " + Format.sec2timeStr(logLine.duration)
                        ToolTip.visible: mouseArea.containsMouse
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
                                    if (text.indexOf("[warning]") >= 0)
                                        return Colors.orange
                                    else if(text.indexOf("[error]") >= 0)
                                        return Colors.red
                                    return palette.text
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

        loading = true
        var xhr = new XMLHttpRequest

        xhr.open("GET", root.source)
        xhr.onreadystatechange = function() {
            // - can't rely on 'Last-Modified' header response to verify
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

    // Parse log-line to see if it contains a time indicator
    // and if yes then turn it into a time value (in seconds)
    function getLogLineTime(line) {
        const regex = /[0-9]{2}:[0-9]{2}:[0-9]{2}/
        const found = line.match(regex)
        if (found && found.length > 0) {
            let hh = parseInt(found[0].substring(0, 2))
            let mm = parseInt(found[0].substring(3, 5))
            let ss = parseInt(found[0].substring(6, 8))
            let time = ss + 60 * mm + 3600 * hh;
            if (!isNaN(time)) {
                return time
            }
        }
        return -1
    }

    // Update a log-lines ListModel from a log-text by filling it with elements containing: 
    // - a log-line (string)
    // - the elapsed time since the last log-line containing a time value and this one (if it also contains a time value)
    function updateLogLinesModel(llm, text) {
        llm.clear()
        const lines = text.split('\n')
        const times = lines.map(line => getLogLineTime(line))
        let prev_idx = -1
        for (let i = 0; i < lines.length; i++) {
            let delta = -1
            if (times[i] >= 0) {
                if (prev_idx >= 0) {
                    delta = times[i]-times[prev_idx]
                }
                prev_idx = i
            }
            llm.append({"line": lines[i], "duration": delta})
        }
    }
}
