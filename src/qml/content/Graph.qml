import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0
import NodeEditor 1.0
import Meshroom.Graph 1.0

Item {

    id: root
    signal selectionChanged(var node)

    Component.onCompleted: {
        editor.init();
        editor.fitLayout();
    }

    Connections {
        target: currentScene.graph
        onNodeAdded: {
            editor.nodes.addNode(node);
            currentScene.setDirty(true);
        }
        onNodeVisitStarted: {
            var nodeID = editor.nodes.getID(node);
            var nodeObj = editor.nodes.get(nodeID);
            nodeObj.modelData.status = Node.WAITING;
        }
        onNodeComputeStarted: {
            var nodeID = editor.nodes.getID(node);
            var nodeObj = editor.nodes.get(nodeID);
            nodeObj.modelData.status = Node.RUNNING;
        }
        onNodeComputeCompleted: {
            var nodeID = editor.nodes.getID(node);
            var nodeObj = editor.nodes.get(nodeID);
            nodeObj.modelData.status = Node.DONE;
        }
        onNodeComputeFailed: {
            var nodeID = editor.nodes.getID(node);
            var nodeObj = editor.nodes.get(nodeID);
            nodeObj.modelData.status = Node.ERROR;
        }
        onConnectionAdded: {
            editor.connections.addConnection(node);
            currentScene.setDirty(true);
        }
        onDescriptionRequested: {
            var nodes = editor.nodes.serializeToJSON();
            var connections = editor.connections.serializeToJSON();
            currentScene.graph.descriptionReceived(nodes, connections);
        }
        onStatusCleared: {
            for(var i = 0; i < editor.nodes.count ; i++)
                editor.nodes.get(i).modelData.status = Node.READY;
        }
        onCleared: { editor.init() }
    }

    property Component contextMenu: Menu {
        signal compute()
        MenuItem {
            text: "Compute..."
            onTriggered: compute()
        }
        MenuSeparator {}
    }

    NodeEditor {
        id: editor
        anchors.fill: parent
        onNodeLeftClicked: root.selectionChanged(node)
        onNodeRightClicked: {
            function compute_CB() {
                currentScene.graph.compute(node.name, Graph.LOCAL);
            }
            var menu = contextMenu.createObject(editor);
            menu.compute.connect(compute_CB);
            menu.popup()
        }
    }

    Text {
        text: currentScene.graph.cacheUrl.toString().replace("file://", "")
        color: Style.text.color.dark
        font.pixelSize: Style.text.size.xsmall
    }
}
