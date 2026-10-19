import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import MaterialIcons 2.2
import Utils 1.0

/**
 * Bar on top of the Graph Editor to navigate in the subgraphs (breadcrumb from the project graph to the
 * entered subgraph) and to run a subgraph live (Run Live).
 * Visible inside a subgraph, or when a SubGraph node is selected.
 */
Rectangle {
    id: root

    property var uigraph: null
    readonly property bool inSubGraph: uigraph ? uigraph.isInSubGraph : false
    readonly property var selectedNode: uigraph ? uigraph.selectedNode : null
    readonly property bool subGraphSelected: uigraph && selectedNode ? uigraph.isSubGraphNode(selectedNode) : false

    visible: inSubGraph || subGraphSelected
    height: visible ? layout.implicitHeight + 6 : 0
    color: Qt.rgba(0.12, 0.12, 0.12, 0.92)

    RowLayout {
        id: layout
        anchors.fill: parent
        anchors.leftMargin: 6
        anchors.rightMargin: 6
        spacing: 2

        MaterialToolButton {
            text: MaterialIcons.arrow_upward
            visible: root.inSubGraph
            font.pointSize: 10
            padding: 2
            ToolTip.text: "Leave the Subgraph (U)"
            ToolTip.visible: hovered
            onClicked: uigraph.exitSubGraph()
        }

        // Breadcrumb: the project graph, then each entered node
        Button {
            text: "Project"
            visible: root.inSubGraph
            flat: true
            padding: 2
            onClicked: uigraph.exitSubGraphTo(0)
        }
        Repeater {
            model: root.inSubGraph ? uigraph.subGraphPath : []
            delegate: RowLayout {
                spacing: 2
                Label {
                    text: MaterialIcons.chevron_right
                    font.family: MaterialIcons.fontFamily
                }
                Button {
                    text: modelData
                    flat: true
                    padding: 2
                    font.bold: index === uigraph.subGraphPath.length - 1
                    // Leave the subgraphs entered from this one
                    onClicked: uigraph.exitSubGraphTo(index + 1)
                }
            }
        }
        Label {
            visible: !root.inSubGraph
            text: root.selectedNode ? root.selectedNode.label : ""
            elide: Text.ElideRight
        }

        Item { Layout.fillWidth: true }

        Label {
            text: uigraph ? uigraph.liveStatus : ""
            elide: Text.ElideRight
            Layout.maximumWidth: root.width * 0.5
            color: !uigraph || uigraph.liveRunning ? palette.text : (uigraph.liveSuccess ? Colors.green : Colors.red)
            opacity: 0.9
            ToolTip.text: text
            ToolTip.visible: statusArea.containsMouse && text
            MouseArea {
                id: statusArea
                anchors.fill: parent
                hoverEnabled: true
                acceptedButtons: Qt.NoButton
            }
        }
        BusyIndicator {
            visible: uigraph ? uigraph.liveRunning : false
            running: visible
            Layout.preferredWidth: 18
            Layout.preferredHeight: 18
        }
        MaterialToolButton {
            text: MaterialIcons.play_circle_outline
            font.pointSize: 12
            padding: 2
            enabled: uigraph ? !uigraph.liveRunning : false
            ToolTip.text: "Run Live: run the subgraph now, in the software of its context, with the inputs of its node\n" +
                          "(first frame of a frame loop)"
            ToolTip.visible: hovered
            onClicked: uigraph.runLive()
        }
    }
}
