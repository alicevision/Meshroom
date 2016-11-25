import QtQuick 2.7
import QtQuick.Layouts 1.3
import QtQuick.Controls 2.0
import QtQuick.Dialogs 1.2

RowLayout {

    id: root

    // properties
    property alias text: textField.text
    property bool selectExisting: true
    property bool selectFolder: false
    property var nameFilters: []
    spacing: 0

    // signals
    signal editingFinished()

    // components
    property Component openFile: FileDialog {
        title: "Please select a folder"
        folder: "/"
        selectExisting: true
        selectFolder: root.selectFolder
        selectMultiple: false
        sidebarVisible: false
        nameFilters: root.nameFilters
    }

    TextField {
        id: textField
        Layout.fillWidth: true
        selectByMouse: true
        onEditingFinished: root.editingFinished()
    }
    ToolButton {
        icon: "qrc:///images/folder.svg"
        onClicked: {
            function _CB() {
                textField.text = dialog.fileUrl.toString().replace("file://", "")
                root.editingFinished()
            }
            var dialog = root.openFile.createObject(parent);
            dialog.onAccepted.connect(_CB);
            dialog.open();
        }
    }

}
