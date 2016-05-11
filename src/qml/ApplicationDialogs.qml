import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import QtQuick.Dialogs 1.2
import DarkStyle.Controls 1.0
import DarkStyle.Dialogs 1.0
import DarkStyle 1.0
import "delegates"

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
    property Component maySaveScene: Dialog {
        title: "Save?"
        content: RowLayout {
            Button {
                Layout.fillWidth: true
                text: "No"
                onClicked: reject()
            }
            Button {
                Layout.fillWidth: true
                text: "Yes"
                onClicked: accept()
            }
        }
    }
    property Component addNode: Dialog {
        property string selection: ""
        title: "New node"
        content: ColumnLayout {
            spacing: 0
            ComboBox {
                id: pluginCombo
                Layout.fillWidth: true
                model: _application.nodeTypes
            }
            Button {
                Layout.fillWidth: true
                text: "Add"
                onClicked: {
                    selection = pluginCombo.currentText;
                    accept();
                }
            }
        }
    }
}
