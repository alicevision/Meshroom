import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0

Rectangle {

    id: root
    property variant inputs: model.inputs
    property variant outputs: model.outputs

    function getInputItem(id) {
        return inputRepeater.itemAt(id);
    }
    function getOutputItem(id) {
        return outputRepeater.itemAt(id);
    }

    radius: 10
    color: Style.window.color.dark
    border.color: mouse.containsMouse ? Style.window.color.selected : Style.window.color.light
    Behavior on border.color { ColorAnimation {}}
    onXChanged: nodeChanged()
    onYChanged: nodeChanged()

    MouseArea { // drag
        id: mouse
        anchors.fill: parent
        drag.target: root
        drag.axis: Drag.XAndYAxis
        drag.minimumX: 0
        drag.maximumX: root.parent.width - root.width
        drag.minimumY: 0
        drag.maximumY: root.parent.height - root.height
        propagateComposedEvents: true
        hoverEnabled: true
        onClicked: selectionChanged(model)
    }

    Text {
        anchors.fill: parent
        text: model.name
        font.pixelSize: Style.text.size.xsmall
        horizontalAlignment: Text.AlignHCenter
    }

    Column {
        anchors.top: parent.top
        anchors.topMargin: 10
        width: parent.width * 0.5
        height: parent.height
        spacing: 2
        Repeater {
            id: inputRepeater
            clip: true
            model: root.inputs
            delegate: RowLayout {
                height: 15
                width: parent.width
                spacing: 0
                Rectangle {
                    Layout.preferredHeight: 15
                    Layout.preferredWidth: 2
                    color: Style.window.color.xlight
                }
                Item { Layout.preferredWidth: 2 } // spacer
                Text {
                    Layout.fillWidth: true
                    text: model.name
                    // color: Style.text.color.dark
                    font.pixelSize: Style.text.size.xsmall
                }
            }
        }
    }

    Column {
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.topMargin: 10
        width: parent.width * 0.5
        height: parent.height
        spacing: 2
        Repeater {
            id: outputRepeater
            clip: true
            model: root.outputs
            delegate: RowLayout {
                height: 15
                width: parent.width
                spacing: 0
                Text {
                    Layout.fillWidth: true
                    text: model.name
                    // color: Style.text.color.dark
                    font.pixelSize: Style.text.size.xsmall
                    horizontalAlignment: Text.AlignRight
                }
                Item { Layout.preferredWidth: 2 } // spacer
                Rectangle {
                    Layout.preferredHeight: 15
                    Layout.preferredWidth: 2
                    color: Style.window.color.xlight
                }
            }
        }
    }

}
