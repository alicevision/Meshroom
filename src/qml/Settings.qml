import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3
import NodeEditor 1.0

Item {

    id : root

    // properties
    property variant graph: null
    property variant node: null

    ListView {
        anchors.fill: parent
        ScrollBar.vertical: ScrollBar {}
        model: (root.node && root.node.inputs) ? root.node.inputs : 0
        spacing: 20
        delegate: ColumnLayout {
            width: ListView.view.width
            Label {
                Layout.fillWidth: true
                text: model.name
                enabled: false
                horizontalAlignment: Text.AlignLeft
                state: "small"
            }
            EditAttributeDelegate {
                Layout.fillWidth: true
                graph: root.graph
                nodeName: root.node.name
                attribute: modelData
            }

        }
    }
}
