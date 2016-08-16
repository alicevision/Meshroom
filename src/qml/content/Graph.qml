import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3
import NodeEditor 1.0
import Meshroom.Graph 1.0 as MG

Item {

    id: root

    // signal / slots
    signal selectionChanged(var node)

    // components
    property Component contextMenu: Menu {
        signal compute(var mode)
        MenuItem {
            text: "Compute locally..."
            onTriggered: compute(MG.Graph.COMPUTE_LOCAL)
        }
        MenuItem {
            text: "Compute on farm..."
            onTriggered: compute(MG.Graph.COMPUTE_TRACTOR)
        }
        MenuItem {
            text: "Refresh status..."
            onTriggered: compute(MG.Graph.PREPARE)
        }
    }

    // node editor
    NodeEditor {
        id: editor
        anchors.fill: parent
        Component.onCompleted: currentScene.graph.setObject(editor.graph)
        onNodeLeftClicked: root.selectionChanged(node)
        onNodeRightClicked: {
            function compute_CB(mode) {
                editor.graph.clearNodeStatuses();
                currentScene.graph.startWorker(mode, node.name);
            }
            var menu = contextMenu.createObject(editor);
            menu.x = node.x+10;
            menu.y = node.y+10;
            menu.compute.connect(compute_CB);
            menu.open()
        }
    }

    Label {
        text: currentScene.graph.cacheUrl.toString().replace("file://", "")
        state: "xsmall"
    }
}
