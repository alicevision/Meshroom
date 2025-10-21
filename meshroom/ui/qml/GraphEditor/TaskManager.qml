import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import MaterialIcons 2.2
import Controls 1.0
import Utils 1.0

Item {
    id: root

    implicitWidth: 500
    implicitHeight: 500

    property var uigraph
    property var taskManager

    SystemPalette { id: activePalette }

    property color textColor: Colors.sysPalette.text
    property color bgColor: Qt.darker(Colors.sysPalette.window, 1.15)
    property color headBgColor: Qt.darker(Colors.sysPalette.window, 1.30)
    property color tableBorder: Colors.sysPalette.window
    property int borderWidth: 3

    property var selectedChunk: null

    function selectNode(node) {
        uigraph.selectedNode = node
    }

    function selectChunk(chunk) {
        root.selectedChunk = chunk
        uigraph.selectedChunk = chunk
    }
    
    TextMetrics {
        id: nbMetrics
        text: root.taskManager ? root.taskManager.nodes.count : "0"
    }

    TextMetrics {
        id: statusMetrics
        text: "SUBMITTED"
    }

    TextMetrics {
        id: chunksMetrics
        text: "Chunks Done"
    }

    TextMetrics {
        id: execMetrics
        text: "Exec Mode"
    }

    TextMetrics {
        id: progressMetrics
        text: "Progress"
    }

    RowLayout {
        anchors.fill: parent

        ColumnLayout {
            Layout.alignment: Qt.AlignLeft | Qt.AlignTop
            width: childrenRect.width

            // TODO : enable/disable buttons depending on selectedChunk
            // TODO : Also handle case where uigraph.selectedNode and selectedNode.chunksCreated==false

            MaterialToolButton {
                ToolTip.text: "Stop task"
                enabled: selectedChunk !== null
                text: MaterialIcons.stop_circle
                font.pointSize: 15
                onClicked: {
                    uigraph.stopTask(selectedChunk)
                }
            }

            MaterialToolButton {
                ToolTip.text: "Pause task"
                enabled: selectedChunk !== null
                text: MaterialIcons.pause_circle_filled
                font.pointSize: 15
                onClicked: {
                    uigraph.pauseTask(selectedChunk)
                }
            }

            MaterialToolButton {
                ToolTip.text: "Restart task"
                enabled: selectedChunk !== null
                text: MaterialIcons.play_circle_filled
                font.pointSize: 15
                onClicked: {
                    uigraph.restartTask(selectedChunk)
                }
            }

            MaterialToolButton {
                ToolTip.text: "Skip task"
                enabled: selectedChunk !== null
                text: MaterialIcons.skip_next
                font.pointSize: 15
                onClicked: {
                    uigraph.skipTask(selectedChunk)
                }
            }
        }

        ListView {
            id: taskList
            Layout.alignment: Qt.AlignLeft | Qt.AlignTop
            Layout.fillWidth: true
            Layout.fillHeight: true
            ScrollBar.vertical: MScrollBar {}

            model: root.taskManager ? root.taskManager.nodes : null
            spacing: 3

            headerPositioning: ListView.OverlayHeader

            header: RowLayout {
                height: 30
                spacing: 3

                width: parent.width

                z: 2

                Label {
                    text: qsTr("Nb")
                    Layout.preferredWidth: nbMetrics.width + 20
                    Layout.preferredHeight: parent.height
                    horizontalAlignment: Label.AlignHCenter
                    verticalAlignment: Label.AlignVCenter
                    background: Rectangle {
                        color: headBgColor
                    }
                }
                Label {
                    text: qsTr("Node")
                    Layout.preferredWidth: 250
                    Layout.preferredHeight: parent.height
                    horizontalAlignment: Label.AlignHCenter
                    verticalAlignment: Label.AlignVCenter
                    background: Rectangle {
                        color: headBgColor
                    }
                }
                Label {
                    text: qsTr("State")
                    Layout.preferredWidth: statusMetrics.width + 20
                    Layout.preferredHeight: parent.height
                    horizontalAlignment: Label.AlignHCenter
                    verticalAlignment: Label.AlignVCenter
                    background: Rectangle {
                        color: headBgColor
                    }
                }
                Label {
                    text: qsTr("Chunks Done")
                    Layout.preferredWidth: chunksMetrics.width + 20
                    Layout.preferredHeight: parent.height
                    horizontalAlignment: Label.AlignHCenter
                    verticalAlignment: Label.AlignVCenter
                    background: Rectangle {
                        color: headBgColor
                    }
                }
                Label {
                    text: qsTr("Exec Mode")
                    Layout.preferredWidth: execMetrics.width + 20
                    Layout.preferredHeight: parent.height
                    horizontalAlignment: Label.AlignHCenter
                    verticalAlignment: Label.AlignVCenter
                    background: Rectangle {
                        color: headBgColor
                    }
                }
                Label {
                    text: qsTr("Progress")
                    Layout.fillWidth: true
                    Layout.minimumWidth: progressMetrics.width + 20
                    Layout.preferredHeight: parent.height
                    horizontalAlignment: Label.AlignHCenter
                    verticalAlignment: Label.AlignVCenter
                    background: Rectangle {
                        color: headBgColor
                    }
                }
            }

            delegate: RowLayout {
                width: ListView.view.width
                height: 18
                spacing: 3

                function getNbFinishedChunks(chunks) {
                    var nbSuccess = 0
                    for (var i = 0; i < chunks.count; i++) {
                        if (chunks.at(i).statusName === "SUCCESS") {
                            nbSuccess += 1
                        }
                    }
                    return nbSuccess
                }

                Label {
                    text: index + 1
                    Layout.preferredWidth: nbMetrics.width + 20
                    Layout.preferredHeight: parent.height
                    horizontalAlignment: Label.AlignHCenter
                    verticalAlignment: Label.AlignVCenter
                    color: object === uigraph.selectedNode ? Colors.sysPalette.window : Colors.sysPalette.text
                    background: Rectangle {
                        color: object === uigraph.selectedNode ? Colors.sysPalette.text : bgColor
                    }

                    MouseArea {
                        anchors.fill: parent
                        onPressed: {
                            selectNode(object)
                        }
                    }
                }
                Label {
                    text: object.label
                    Layout.preferredWidth: 250
                    Layout.preferredHeight: parent.height
                    horizontalAlignment: Label.AlignHCenter
                    verticalAlignment: Label.AlignVCenter
                    color: object === uigraph.selectedNode ? Colors.sysPalette.window : Colors.sysPalette.text
                    background: Rectangle {
                        color: object === uigraph.selectedNode ? Colors.sysPalette.text : bgColor
                    }

                    MouseArea {
                        anchors.fill: parent
                        acceptedButtons: Qt.LeftButton | Qt.RightButton
                        onPressed: (mouse) => {
                            if (mouse.button === Qt.LeftButton) {
                                selectNode(object)
                            } else if (mouse.button === Qt.RightButton) {
                                contextMenu.popup()
                            }
                        }
                        Menu {
                            id: contextMenu
                            MenuItem {
                                text: "Open Folder"
                                height: visible ? implicitHeight : 0
                                onTriggered: Qt.openUrlExternally(Filepath.stringToUrl(object.internalFolder))
                            }
                        }
                    }
                }
                Label {
                    text: object.globalStatus
                    Layout.preferredWidth: statusMetrics.width + 20
                    Layout.preferredHeight: parent.height
                    horizontalAlignment: Label.AlignHCenter
                    verticalAlignment: Label.AlignVCenter
                    color: object === uigraph.selectedNode ? Colors.sysPalette.window : Colors.sysPalette.text
                    background: Rectangle {
                        color: object === uigraph.selectedNode ? Colors.sysPalette.text : bgColor
                    }

                    MouseArea {
                        anchors.fill: parent
                        onPressed: {
                            selectNode(object)
                        }
                    }
                }
                Label {
                    text: getNbFinishedChunks(object.chunks) + "/" + object.chunks.count
                    Layout.preferredWidth: chunksMetrics.width + 20
                    Layout.preferredHeight: parent.height
                    horizontalAlignment: Label.AlignHCenter
                    verticalAlignment: Label.AlignVCenter
                    color: object === uigraph.selectedNode ? Colors.sysPalette.window : Colors.sysPalette.text
                    background: Rectangle {
                        color: object === uigraph.selectedNode ? Colors.sysPalette.text : bgColor
                    }

                    MouseArea {
                        anchors.fill: parent
                        onPressed: {
                            selectNode(object)
                        }
                    }
                }
                Label {
                    text: object.globalExecMode
                    Layout.preferredWidth: execMetrics.width + 20
                    Layout.preferredHeight: parent.height
                    horizontalAlignment: Label.AlignHCenter
                    verticalAlignment: Label.AlignVCenter
                    color: object === uigraph.selectedNode ? Colors.sysPalette.window : Colors.sysPalette.text
                    background: Rectangle {
                        color: object === uigraph.selectedNode ? Colors.sysPalette.text : bgColor
                    }

                    MouseArea {
                        anchors.fill: parent
                        onPressed: {
                            selectNode(object)
                        }
                    }
                }
                Item {
                    Layout.fillWidth: true
                    Layout.minimumWidth: progressMetrics.width + 20
                    Layout.preferredHeight: parent.height

                    ListView {
                        id: chunkList
                        width: parent.width
                        height: parent.height
                        orientation: ListView.Horizontal
                        model: object.chunks
                        property var node: object

                        spacing: 3

                        delegate: Loader {
                            id: chunkDelegate
                            width: ListView.view.model ? (ListView.view.width / ListView.view.model.count) - 3 : 0
                            height: ListView.view.height

                            function getChunkBorderColor() {
                                if (chunkList.node === uigraph.selectedNode) {
                                    if (root.selectedChunk == object)
                                        return Colors.sysPalette.text
                                    else
                                        return Qt.darker(Colors.sysPalette.text, 1.3)
                                } else {
                                    return "transparent"
                                }
                            }

                            sourceComponent: Label {
                                anchors.fill: parent
                                background: Rectangle {
                                    color: Colors.getChunkColor(object, {"NONE": bgColor})
                                    radius: 3
                                    border.width: 2
                                    border.color: chunkDelegate.getChunkBorderColor()
                                }

                                MouseArea {
                                    anchors.fill: parent
                                    onPressed: {
                                        selectNode(chunkList.node)
                                        selectChunk(object)
                                    }
                                }
                            }
                        }

                        // Placeholder for uninitialized chunks
                        Label {
                            enabled: chunkList.model.count == 0
                            visible: enabled
                            anchors.fill: parent
                            background: Rectangle {
                                color: Colors.darkpurple  // TODO : Use Colors.statusColors[nodeStatus]
                                radius: 3
                                border.width: 2
                                border.color: chunkList.node === uigraph.selectedNode ? Colors.sysPalette.text : "transparent"
                            }

                            MouseArea {
                                anchors.fill: parent
                                onPressed: {
                                    selectNode(chunkList.node)
                                    selectChunk(null)
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
