import QtQuick 2.9
import QtQuick.Layouts 1.3
import QtQuick.Controls 2.2

/**
  A component to display and edit a Node's attributes.
*/
ColumnLayout {
    id: root

    property variant node: null  // the node to edit
    property bool readOnly: false

    SystemPalette { id: palette }

    Button {
        text: "Open Node Folder"
        onClicked: Qt.openUrlExternally("file://" + node.internalFolder)
        ToolTip.text: node.internalFolder
        ToolTip.visible: hovered
    }

    ListView {
        id: attributesListView

        Layout.fillHeight: true
        Layout.fillWidth: true
        clip: true
        spacing: 4
        ScrollBar.vertical: ScrollBar { id: scrollBar }

        model: node ? node.attributes : undefined

        delegate: RowLayout {
            width: attributesListView.width
            spacing: 4

            Label {
                id: parameterLabel
                text: object.label
                Layout.preferredWidth: 200
                color: object.isOutput ? "orange" : palette.text
                ToolTip.text: object.desc.description
                ToolTip.visible: parameterMA.containsMouse
                ToolTip.delay: 200
                MouseArea {
                    id: parameterMA
                    anchors.fill: parent
                    hoverEnabled: true
                }
            }

            AttributeItemDelegate {
                Layout.fillWidth: true
                Layout.rightMargin: scrollBar.width
                height: childrenRect.height
                attribute: object
                readOnly: root.readOnly
            }
        }
    }
}
