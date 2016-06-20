import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0
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
            onTriggered: compute(MG.Graph.LOCAL)
        }
        MenuItem {
            text: "Compute on farm..."
            onTriggered: compute(MG.Graph.TRACTOR)
        }
        MenuSeparator {}
    }

    // node editor
    NodeEditor {
        id: editor
        anchors.fill: parent
        Component.onCompleted: currentScene.graph.setObject(editor.graph)
        onNodeLeftClicked: root.selectionChanged(node)
        onNodeRightClicked: {
            function compute_CB(mode) {
                currentScene.graph.startWorker(node.name, mode);
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
