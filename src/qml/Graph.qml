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
        signal remove()
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
        Rectangle { // spacer
            width: parent.width; height: 1
            color: Qt.rgba(1, 1, 1, 0.1)
        }
        MenuItem {
            text: "Delete node"
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
        anchors.fill: parent
        onClicked: selectionChanged(null)
    }

    // node editor
    NodeEditor {
        id: editor
        anchors.fill: parent
        onNodeLeftClicked: root.selectionChanged(node)
        onNodeRightClicked: {
            function compute_CB(mode) {
                editor.graph.clearNodeStatuses();
                currentScene.graph.startWorker(mode, node.name);
            }
            function remove_CB(mode) {
                // todo
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
