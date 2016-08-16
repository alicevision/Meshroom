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
                Button {
                    Layout.fillWidth: true
                    text: "Yes"
                    onClicked: { accepted(); close(); }
                }
                Button {
                    Layout.fillWidth: true
                    text: "No"
                    onClicked: { rejected(); close(); }
                }
                Button {
                    Layout.fillWidth: true
                    text: "Cancel"
                    onClicked: { close(); }
                }
            }
        }
    }
    property Component addNode: Popup {
        signal accepted(var selection)
        signal rejected()
        ColumnLayout {
            anchors.fill: parent
            spacing: 0
            ListView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                model: _application.pluginNodes
                delegate: Button {
                    width: parent.width
                    text: modelData.plugin + "/" + modelData.type
                    onClicked: { accepted(modelData.metadata); close(); }
                }
            }
            Button {
                Layout.fillWidth: true
                text: "Cancel"
                onClicked: { rejected(); close(); }
            }
        }
    }
}
