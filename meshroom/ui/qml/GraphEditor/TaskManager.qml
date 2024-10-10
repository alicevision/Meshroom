import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

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

    function selectNode(node) {
        uigraph.selectedNode = node
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

    ListView {
        id: taskList
        anchors.fill: parent
        ScrollBar.vertical: MScrollBar {}

        model: parent.taskManager ? parent.taskManager.nodes : null
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
                    onPressed: {
                        selectNode(object)
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

                    delegate: Label {
                        width: ListView.view.model ? (ListView.view.width / ListView.view.model.count) - 3 : 0
                        height: ListView.view.height
                        anchors.verticalCenter: parent.verticalCenter
                        background: Rectangle {
                            color: Colors.getChunkColor(object, {"NONE": bgColor})
                            radius: 3
                            border.width: 2
                            border.color: chunkList.node === uigraph.selectedNode ? Colors.sysPalette.text : Colors.getChunkColor(object, {"NONE": bgColor})
                        }

                        MouseArea {
                            anchors.fill: parent
                            onPressed: {
                                selectNode(chunkList.node)
                            }
                        }
                    }
                }
            }
        }
    }
}
