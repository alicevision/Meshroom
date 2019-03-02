import QtQuick 2.9
import QtQuick.Controls 2.3
import MaterialIcons 2.2

/// Meshroom "Add Node" window
Dialog {
    id: root

    property string nodeType
    property string info
    property bool addNodeMode
    property var createNode

    x: parent.width / 2 - width / 2
    y: parent.height / 2 - height / 2
    width: 1000

    parent: ApplicationWindow.overlay

    // Fade in transition
    enter: Transition {
        NumberAnimation { property: "opacity"; from: 0.0; to: 1.0 }
    }

    modal: true
    closePolicy: Dialog.CloseOnEscape | Dialog.CloseOnPressOutside
    padding: 30
    topPadding: 25

    header: Pane {
        background: Item {}
        MaterialToolButton {
            text: MaterialIcons.close
            anchors.right: parent.right
            onClicked: root.close()
        }
        Label {
            id:title
            text: nodeType
        }
    }

    contentItem: GroupBox {
        id: information
        title: "Information"
        TextArea {
            id: showntext
            property string selectedName: "none"
            width: parent.width
            wrapMode: TextEdit.Wrap
            readOnly: true
            text: root.info
        }
    }

    footer: Button {
        id: addNode
        enabled: addNodeMode
        visible: enabled
        text: "Add"
        onClicked: { 
            root.createNode(root.nodeType)
            root.close()
        }
    }
}

