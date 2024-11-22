import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

/**
 * NodeStatus displays the status-related information of Node's chunks (NodeChunks)
 *
 * To ease monitoring, it provides periodic auto-reload of the opened file
 * if the related NodeChunk is being computed.
 */

FocusScope {
    id: root
    property variant node
    property variant currentChunkIndex
    property variant currentChunk

    SystemPalette { id: activePalette }

    Loader {
        id: componentLoader
        clip: true
        anchors.fill: parent

        property string currentFile: (root.currentChunkIndex >= 0) ? root.currentChunk["statusFile"] : ""
        property url sourceFile: Filepath.stringToUrl(currentFile)

        sourceComponent: statViewerComponent
    }

    Component {
        id: statViewerComponent
        Item {
            id: statusViewer
            property url source: componentLoader.sourceFile
            property var lastModified: undefined

            onSourceChanged: {
                statusListModel.readSourceFile()
            }

            ListModel {
                id: statusListModel

                function readSourceFile() {
                    // Make sure we are trying to load a statistics file
                    if (!Filepath.urlToString(source).endsWith("status"))
                        return

                    var xhr = new XMLHttpRequest
                    xhr.open("GET", source)

                    xhr.onreadystatechange = function() {
                        if (xhr.readyState === XMLHttpRequest.DONE && xhr.status === 200) {
                            if (lastModified === undefined || lastModified !== xhr.getResponseHeader('Last-Modified')) {
                                lastModified = xhr.getResponseHeader('Last-Modified')
                                try {
                                    var jsonObject = JSON.parse(xhr.responseText)

                                    var entries = []
                                    // Prepare data to populate the ListModel from the input json object
                                    for (var key in jsonObject) {
                                        var entry = {}
                                        entry["key"] = key
                                        entry["value"] = String(jsonObject[key])
                                        entries.push(entry)
                                    }
                                    // Reset the model with prepared data (limit to one update event)
                                    statusListModel.clear()
                                    statusListModel.append(entries)
                                } catch(exc) {
                                    lastModified = undefined
                                    statusListModel.clear()
                                }
                            }
                        } else {
                            lastModified = undefined
                            statusListModel.clear()
                        }
                    }
                    xhr.send()
                }
            }

            ListView {
                id: statusListView
                anchors.fill: parent
                spacing: 3
                model: statusListModel

                delegate: Rectangle {
                    color: activePalette.window
                    width: parent.width
                    height: childrenRect.height
                    RowLayout {
                        width: parent.width
                        Rectangle {
                            id: statusKey
                            anchors.margins: 2
                            color: Qt.darker(activePalette.window, 1.1)
                            Layout.preferredWidth: sizeHandle.x
                            Layout.minimumWidth: 10.0 * Qt.application.font.pixelSize
                            Layout.maximumWidth: 15.0 * Qt.application.font.pixelSize
                            Layout.fillWidth: false
                            Layout.fillHeight: true
                            Label {
                                text: key
                                anchors.fill: parent
                                anchors.top: parent.top
                                topPadding: 4
                                leftPadding: 6
                                verticalAlignment: TextEdit.AlignTop
                                elide: Text.ElideRight
                            }
                        }
                        TextArea {
                            id: statusValue
                            text: value
                            anchors.margins: 2
                            Layout.fillWidth: true
                            wrapMode: Label.WrapAtWordBoundaryOrAnywhere
                            textFormat: TextEdit.PlainText

                            readOnly: true
                            selectByMouse: true
                            background: Rectangle { anchors.fill: parent; color: Qt.darker(activePalette.window, 1.05) }
                        }
                    }
                }
            }

            // Categories resize handle
            Rectangle {
                id: sizeHandle
                height: parent.contentHeight
                width: 1
                x: parent.width * 0.2
                MouseArea {
                    anchors.fill: parent
                    anchors.margins: -4
                    cursorShape: Qt.SizeHorCursor
                    drag {
                        target: parent
                        axis: Drag.XAxis
                        threshold: 0
                        minimumX: statusListView.width * 0.2
                        maximumX: statusListView.width * 0.8
                    }
                }
            }
        }
    }
}
