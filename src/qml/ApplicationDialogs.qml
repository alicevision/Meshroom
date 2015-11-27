import QtQuick 2.5
import QtQuick.Dialogs 1.2

Item {

    property variant openProject: FileDialog {
        title: "Please choose a project directory"
        folder: "/"
        selectFolder: true
        selectMultiple: false
        sidebarVisible: false
        onAccepted: openProject(fileDialog.fileUrl)
    }

}
