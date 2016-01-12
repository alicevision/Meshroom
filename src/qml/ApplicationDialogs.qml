import QtQuick 2.5
import QtQuick.Dialogs 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0

Item {

    property variant openProject: FileDialog {
        title: "Please choose a project directory"
        folder: "/"
        selectFolder: true
        selectMultiple: false
        sidebarVisible: false
        onAccepted: addProject(fileUrl)
    }

    property variant openProjectSettings: Dialog {
        id: projectSettingsDialog
        title: "Project settings"
        onAccepted: close()
        contentItem: Rectangle {
            color: Style.window.color.xdark
            implicitWidth: _appWindow.width
            implicitHeight: _appWindow.height *0.6
            Text {
                text: "project settings"
                anchors.centerIn: parent
            }
            Button {
                text: "Ok"
                iconSource: "qrc:///images/disk.svg"
                onClicked: projectSettingsDialog.accept()
            }
        }
    }

}
