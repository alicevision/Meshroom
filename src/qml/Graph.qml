import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3
import NodeEditor 1.0
import Meshroom.Worker 1.0

Frame {

    id: root

    // signals
    signal selectionChanged(var node)

    // slots
    Keys.onPressed: {
        if(event.key == Qt.Key_F) {
            editor.fit();
            event.accepted = true;
        }
    }

    // context menus
    property Component nodeContextMenu: Menu {
        signal display()
        signal compute(var mode)
        signal remove()
        MenuItem {
            text: "Show"
            onTriggered: display()
        }
        Rectangle { // spacer
            width: parent.width; height: 1
            color: Qt.rgba(1, 1, 1, 0.1)
        }
        MenuItem {
            text: "Compute locally..."
            onTriggered: compute(Worker.COMPUTE_LOCAL)
        }
        MenuItem {
            text: "Compute on farm..."
            onTriggered: compute(Worker.COMPUTE_TRACTOR)
        }
        MenuItem {
            text: "Refresh node status..."
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
    background: Rectangle {
        color: Qt.rgba(0.3, 0.3, 0.3, 0.1)
        Image {
            anchors.fill: parent
            source: "qrc:///images/stripes.png"
            fillMode: Image.Tile
            opacity: 0.5
        }
    }

    // main content
    NodeEditor {
        id: editor
        anchors.fill: parent
        focus: true
        graph: currentScene.graph
        onWorkspaceMoved: {
            root.forceActiveFocus()
        }
        onWorkspaceClicked: {
            root.forceActiveFocus()
            root.selectionChanged(null)
        }
        onNodeMoved: {
            root.forceActiveFocus()
        }
        onNodeLeftClicked: {
            root.forceActiveFocus()
            root.selectionChanged(node)
        }
        onNodeRightClicked: {
            root.forceActiveFocus()
            var menu = nodeContextMenu.createObject(item);
            menu.display.connect(function display_CB() {
                displayAttribute(node.outputs.data(node.outputs.index(0,0), AttributeCollection.ModelDataRole))
            });
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
        onEdgeLeftClicked: {
            root.forceActiveFocus()
        }
        onEdgeRightClicked: {
            root.forceActiveFocus()
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
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        enabled: false
        text: currentScene.graph.cacheUrl.toString().replace("file://", "")
        state: "xsmall"
    }
}
