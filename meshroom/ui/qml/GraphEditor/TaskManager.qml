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

    // Max width for some columns
    readonly property int maxExecWidth: 200

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

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // TODO : enable/disable buttons depending on selectedChunk
        // TODO : Also handle case where uigraph.selectedNode and selectedNode.chunksCreated==false

        // Task / Job toolbar
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: toolbarRow.implicitHeight + 4
            color: root.headBgColor

            RowLayout {
                id: toolbarRow
                anchors.fill: parent
                anchors.leftMargin: 4
                anchors.rightMargin: 4
                spacing: 2

                Label {
                    text: qsTr("Task")
                    font.bold: true
                    color: Colors.sysPalette.mid
                    Layout.rightMargin: 2
                }

                MaterialToolButton {
                    ToolTip.text: "Stop Task"
                    enabled: selectedChunk !== null || root.uigraph.selectedNode !== null
                    text: MaterialIcons.stop_circle
                    font.pointSize: 15
                    onClicked: {
                        if (selectedChunk !== null) {
                            root.uigraph.stopTask(selectedChunk)
                        } else {
                            root.uigraph.stopNode(root.uigraph.selectedNode)
                        }
                    }
                }

                MaterialToolButton {
                    ToolTip.text: "Restart Task"
                    enabled: selectedChunk !== null
                    text: MaterialIcons.replay_circle_filled
                    font.pointSize: 15
                    onClicked: uigraph.restartTask(selectedChunk)
                }

                MaterialToolButton {
                    ToolTip.text: "Skip Task"
                    enabled: selectedChunk !== null
                    text: MaterialIcons.skip_next
                    font.pointSize: 15
                    onClicked: uigraph.skipTask(selectedChunk)
                }

                Rectangle {
                    Layout.preferredWidth: 1
                    Layout.preferredHeight: 20
                    Layout.leftMargin: 6
                    Layout.rightMargin: 6
                    color: Colors.sysPalette.mid
                }

                Label {
                    text: qsTr("Job")
                    font.bold: true
                    color: Colors.sysPalette.mid
                    Layout.rightMargin: 2
                }

                MaterialToolButton {
                    ToolTip.text: "Pause Job"
                    enabled: root.uigraph.selectedNode !== null
                    text: MaterialIcons.pause_circle_filled
                    font.pointSize: 15
                    onClicked: uigraph.pauseJob(uigraph.selectedNode)
                }

                MaterialToolButton {
                    ToolTip.text: "Resume Job"
                    enabled: root.uigraph.selectedNode !== null
                    text: MaterialIcons.play_circle_filled
                    font.pointSize: 15
                    onClicked: uigraph.resumeJob(uigraph.selectedNode)
                }

                MaterialToolButton {
                    ToolTip.text: "Interrupt Job"
                    enabled: root.uigraph.selectedNode !== null
                    text: MaterialIcons.stop_circle
                    font.pointSize: 15
                    onClicked: uigraph.interruptJob(uigraph.selectedNode)
                }

                MaterialToolButton {
                    ToolTip.text: "Restart All Error Tasks"
                    enabled: root.uigraph.selectedNode !== null
                    text: MaterialIcons.replay_circle_filled
                    font.pointSize: 15
                    onClicked: uigraph.restartJobErrorTasks(uigraph.selectedNode)
                }

                Item { Layout.fillWidth: true }
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
                    Layout.preferredWidth: 200
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
                    Layout.preferredWidth: execMetrics.width + 60
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
                    elide: Text.ElideRight
                    Layout.preferredWidth: 200
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
                    text: object.jobName
                    elide: Text.ElideRight
                    Layout.preferredWidth: execMetrics.width + 60
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
                            width: ListView.view.model 
                                ? (ListView.view.width - (ListView.view.model.count - 1) * chunkList.spacing) / ListView.view.model.count
                                : 0

                            height: ListView.view.height

                            sourceComponent: Label {
                                anchors.fill: parent
                                background: Rectangle {
                                    color: Colors.getChunkColor(object, {"NONE": bgColor})
                                    radius: 3
                                    border.width: 2
                                    border.color: (root.selectedChunk == object) ? Qt.darker(color, 1.3) : "transparent"
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
                                color: Colors.getNodeColor(chunkList.node, {"NONE": Colors.darkpurple})
                                radius: 3
                                border.width: 2
                                border.color: (chunkList.node === uigraph.selectedNode) ? Qt.lighter(color, 1.3) : "transparent"
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
