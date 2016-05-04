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
        currentScene.graph.reload();
        editor.fitLayout();
    }

    Connections {
        target: currentScene.graph
        onNodeAdded: {
            editor.nodes.addNode(name);
            currentScene.setDirty(true);
        }
        onConnectionAdded: {
            editor.connections.addConnection(source, target, slot);
            currentScene.setDirty(true);
        }
    }

    NodeEditor {
        id: editor
        anchors.fill: parent
        onSelectionChanged: root.selectionChanged(node)
    }
}
