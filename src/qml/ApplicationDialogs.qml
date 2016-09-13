import QtQuick 2.7
import QtQuick.Layouts 1.3
import QtQuick.Controls 2.0
import QtQuick.Dialogs 1.2

Item {

    property Component openScene: FileDialog {
        title: "Please select a meshroom file"
        folder: "/"
        selectExisting: true
        selectFolder: false
        selectMultiple: false
        sidebarVisible: false
        nameFilters: [ "Meshroom file (*.meshroom)" ]
    }
    property Component saveScene: FileDialog {
        title: "Please select a meshroom file"
        folder: "/"
        selectExisting: false
        selectFolder: false
        selectMultiple: false
        sidebarVisible: false
        nameFilters: [ "Meshroom file (*.meshroom)" ]
    }
    property Component maySaveScene: Popup {
        signal accepted()
        signal rejected()
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 10
            Label {
                text: "Do you want to save changes?"
            }
            RowLayout {
                Item { Layout.fillWidth: true }
                Button {
                    text: "Yes"
                    onClicked: { accepted(); close(); }
                }
                Button {
                    text: "No"
                    onClicked: { rejected(); close(); }
                }
                Button {
                    text: "Cancel"
                    onClicked: { close(); }
                }
            }
        }
        ToolButton {
            anchors.horizontalCenter: parent.right
            anchors.verticalCenter: parent.top
            icon: "qrc:///images/close.svg"
            onClicked: { close(); }
        }
    }
    property Component addNode: Popup {
        signal accepted(var selection)
        signal rejected()
        ListView {
            anchors.fill: parent
            model: _application.pluginNodes
            ScrollBar.vertical: ScrollBar { active: true }
            delegate: Button {
                width: parent.width
                text: modelData.plugin + "/" + modelData.type
                onClicked: { accepted(modelData.metadata); close(); }
            }
            clip: true
        }
        ToolButton {
            anchors.horizontalCenter: parent.right
            anchors.verticalCenter: parent.top
            icon: "qrc:///images/close.svg"
            onClicked: { rejected(); close(); }
        }
    }
}
