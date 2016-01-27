import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
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

    property variant projectSettingsDialog: Dialog {
        id: projectSettingsDialog
        title: "Project settings"
        onAccepted: close()
        contentItem: Rectangle {
            color: Style.window.color.dark
            implicitWidth: Math.min(_appWindow.width, 600)
            implicitHeight: _appWindow.height*0.5
            ToolButton {
                anchors.top: parent.top
                anchors.right: parent.right
                iconSource: "qrc:///images/close.svg"
                onClicked: projectSettingsDialog.reject()
            }
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 10
                Text {
                    font.pixelSize: Style.text.size.large
                    text: projectSettingsDialog.title
                }
                GridLayout {
                    columns: 2
                    columnSpacing: 20
                    Text {
                        Layout.preferredWidth: 60
                        font.pixelSize: Style.text.size.small
                        horizontalAlignment: Text.AlignRight
                        text: "name :"
                    }
                    TextField {
                        Layout.fillWidth: true
                        text: currentProject.name
                    }
                    Text {
                        Layout.preferredWidth: 60
                        font.pixelSize: Style.text.size.small
                        horizontalAlignment: Text.AlignRight
                        text: "location :"
                    }
                    TextField {
                        Layout.fillWidth: true
                        text: currentProject.url.toString().replace("file://", "")
                        enabled: false
                    }
                }
                Button {
                    Layout.fillWidth: true
                    text: "OK"
                    onClicked: projectSettingsDialog.accept()
                }
            }
        }
    }

    property variant jobSettingsDialog: Dialog {
        id: jobSettingsDialog
        title: "Job settings"
        onAccepted: close()
        contentItem: Rectangle {
            color: Style.window.color.dark
            implicitWidth: Math.min(_appWindow.width, 600)
            implicitHeight: _appWindow.height*0.5
            ToolButton {
                anchors.top: parent.top
                anchors.right: parent.right
                iconSource: "qrc:///images/close.svg"
                onClicked: jobSettingsDialog.reject()
            }
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 10
                Text {
                    font.pixelSize: Style.text.size.large
                    text: jobSettingsDialog.title
                }
                GridLayout {
                    columns: 2
                    columnSpacing: 20
                    Text {
                        Layout.preferredWidth: 60
                        font.pixelSize: Style.text.size.small
                        horizontalAlignment: Text.AlignRight
                        text: "name :"
                    }
                    TextField {
                        Layout.fillWidth: true
                        text: currentJob.name
                    }
                    Text {
                        Layout.preferredWidth: 60
                        font.pixelSize: Style.text.size.small
                        horizontalAlignment: Text.AlignRight
                        text: "location :"
                    }
                    TextField {
                        Layout.fillWidth: true
                        text: currentJob.url.toString().replace("file://", "")
                        enabled: false
                    }
                }
                Button {
                    Layout.fillWidth: true
                    text: "OK"
                    onClicked: jobSettingsDialog.accept()
                }
            }
        }
    }

    property variant jobSubmissionDialog: Dialog {
        id: jobSubmissionDialog
        title: "Job submission"
        onAccepted: close()
        contentItem: Rectangle {
            color: Style.window.color.dark
            implicitWidth: Math.min(_appWindow.width, 600)
            implicitHeight: _appWindow.height*0.5
            ToolButton {
                anchors.top: parent.top
                anchors.right: parent.right
                iconSource: "qrc:///images/close.svg"
                onClicked: jobSubmissionDialog.reject()
            }
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 10
                Text {
                    font.pixelSize: Style.text.size.large
                    text: jobSubmissionDialog.title
                }
                GridLayout {
                    columns: 2
                    columnSpacing: 20
                    Text {
                        Layout.preferredWidth: 60
                        font.pixelSize: Style.text.size.small
                        horizontalAlignment: Text.AlignRight
                        text: "mode :"
                    }
                    RowLayout {
                        ExclusiveGroup { id: radioGroup }
                        RadioButton {
                            Layout.fillWidth: true
                            text: "Local"
                            checked: true
                            exclusiveGroup: radioGroup
                        }
                        RadioButton {
                            Layout.fillWidth: true
                            text: "Farm"
                            exclusiveGroup: radioGroup
                        }
                    }
                    Text {
                        Layout.preferredWidth: 60
                        font.pixelSize: Style.text.size.small
                        horizontalAlignment: Text.AlignRight
                        text: "title :"
                    }
                    TextField {
                        Layout.fillWidth: true
                        text: "job_001"
                    }
                }
                RowLayout {
                    Button {
                        Layout.fillWidth: true
                        text: "CANCEL"
                        onClicked: jobSubmissionDialog.reject()
                    }
                    Button {
                        Layout.fillWidth: true
                        text: "SUBMIT"
                        onClicked: {
                            //submitJob(radioGroup.current.text=="Local");
                            jobSubmissionDialog.accept();
                        }
                    }
                }
            }
        }
    }

    property variant jobDeletionDialog: Dialog {
        id: jobDeletionDialog
        title: "Delete job "+currentJob.name+"?"
        onAccepted: {
            currentJob.modelData.erase();
            currentProject.jobs.removeJob(currentJob.modelData);
            close();
        }
        onRejected: close()
        contentItem: Rectangle {
            color: Style.window.color.warning
            implicitWidth: Math.min(_appWindow.width, 600)
            implicitHeight: _appWindow.height*0.5
            ToolButton {
                anchors.top: parent.top
                anchors.right: parent.right
                iconSource: "qrc:///images/close.svg"
                onClicked: jobDeletionDialog.reject()
            }
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 10
                Text {
                    font.pixelSize: Style.text.size.large
                    text: jobDeletionDialog.title
                }
                RowLayout {
                    Button {
                        Layout.fillWidth: true
                        text: "CANCEL"
                        onClicked: jobDeletionDialog.reject()
                    }
                    Button {
                        Layout.fillWidth: true
                        text: "DELETE"
                        onClicked: jobDeletionDialog.accept();
                    }
                }
            }
        }
    }

}
