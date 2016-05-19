import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0
import NodeEditor 1.0

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
        onConnectionAdded: {
            editor.connections.addConnection(node);
            currentScene.setDirty(true);
        }
        onDescriptionRequested: {
            var nodes = editor.nodes.serializeToJSON();
            var connections = editor.connections.serializeToJSON();
            currentScene.graph.descriptionReceived(nodes, connections);
        }
        onReset: { editor.init() }
    }

    NodeEditor {
        id: editor
        anchors.fill: parent
        onSelectionChanged: root.selectionChanged(node)
    }
}
