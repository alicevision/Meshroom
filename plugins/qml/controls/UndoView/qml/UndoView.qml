import QtQuick 2.7
import QtQuick.Controls 2.0
import UndoView 1.0

Item {
    property alias undoStack: stack.undoStack

    UndoStack {
        id: stack
    }

    ListView {
        anchors.fill: parent
        model: stack.commands
        delegate: Text {
            text: qtObject.text
            width: parent.width
            font.italic: index >= stack.index
            color: index >= stack.index ? "grey" : "#CCC"
            MouseArea {
                anchors.fill: parent
                onClicked: stack.index = index + 1
            }
        }
        ScrollIndicator.vertical: ScrollIndicator {}
    }
    FocusScope {}
}
