import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3
import NodeEditor 1.0
import Meshroom.Worker 1.0

Item {

    id: root

    // signal / slots
    signal selectionChanged(var node)

    // context menus
    property Component nodeContextMenu: Menu {
        signal compute(var mode)
        signal remove()
        MenuItem {
            text: "Compute locally..."
            onTriggered: compute(Worker.COMPUTE_LOCAL)
        }
        MenuItem {
            text: "Compute on farm..."
            onTriggered: compute(Worker.COMPUTE_TRACTOR)
        }
        MenuItem {
            text: "Refresh status..."
            onTriggered: compute(Worker.PREPARE)
        }
        Rectangle { // spacer
            width: parent.width; height: 1
            color: Qt.rgba(1, 1, 1, 0.1)
        }
        MenuItem {
            text: "Delete node"
            onTriggered: remove()
        }
    }
    property Component edgeContextMenu: Menu {
        signal remove()
        MenuItem {
            text: "Delete edge"
            onTriggered: remove()
        }
    }

    // background
    Rectangle {
        anchors.fill: parent
        color: Qt.rgba(0.3, 0.3, 0.3, 0.1)
        Image {
            anchors.fill: parent
            source: "qrc:///images/stripes.png"
            fillMode: Image.Tile
            opacity: 0.5
        }
    }

    // mouse area
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        onClicked: selectionChanged(null)
    }

    // node editor
    NodeEditor {
        id: editor
        anchors.fill: parent
        graph: currentScene.graph
        onWorkspaceClicked: root.selectionChanged(null)
        onNodeLeftClicked: root.selectionChanged(node)
        onNodeRightClicked: {
            var menu = nodeContextMenu.createObject(item);
            menu.compute.connect(function compute_CB(mode) {
                currentScene.graph.startWorkerThread(mode, node.name);
            });
            menu.remove.connect(function remove_CB() {
                currentScene.graph.removeNode(node.serializeToJSON());
            });
            menu.x = pos.x;
            menu.y = pos.y;
            menu.open()
        }
        onEdgeRightClicked: {
            var menu = edgeContextMenu.createObject(item);
            var p = item.mapToItem(root, item.x, item.y);
            menu.remove.connect(function remove_CB() {
                currentScene.graph.removeEdge(edge.serializeToJSON());
            });
            menu.x = pos.x;
            menu.y = pos.y;
            menu.open()
        }
    }

    Label {
        text: currentScene.graph.cacheUrl.toString().replace("file://", "")
        state: "xsmall"
    }
}
