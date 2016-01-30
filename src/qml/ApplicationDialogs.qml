import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import QtQuick.Dialogs 1.2
import DarkStyle.Controls 1.0
import DarkStyle.Dialogs 1.0
import DarkStyle 1.0
import "delegates"

Item {

    property Component dialogModel: Dialog {
        title: "test"
        content: Rectangle {
            color: "red"
        }
    }

    property Component openProject: FileDialog {
        title: "Please choose a project directory"
        folder: "/"
        selectFolder: true
        selectMultiple: false
        sidebarVisible: false
        onAccepted: addProject(fileUrl)
    }

    property Component projectSettingsDialog: Dialog {
        title: "Project settings"
        content: Item {
            GridLayout {
                anchors.fill: parent
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
                    onEditingFinished: currentProject.name = text
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
                Item { Layout.fillHeight: true } // spacer
            }
        }
    }

    property Component jobSettingsDialog: Dialog {
        title: "Job settings"
        content: Item {
            GridLayout {
                anchors.fill: parent
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
                    onEditingFinished: currentJob.name = text
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
                Item { Layout.fillHeight: true } // spacer
            }
        }
    }


    property Component jobSubmissionDialog: Dialog {
        title: "Job submission"
        content: ColumnLayout {
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
                Item { Layout.fillHeight: true } // spacer
            }
            RowLayout {
                spacing: 0
                Button {
                    Layout.fillWidth: true
                    text: "CANCEL"
                    onClicked: reject()
                }
                Button {
                    Layout.fillWidth: true
                    text: "SUBMIT"
                    onClicked: {
                        submitJob(radioGroup.current.text == "Local");
                        accept();
                    }
                }
            }
        }
    }

    property Component jobDeletionDialog: Dialog {
        title: "Delete job "+currentJob.name+"?"
        backgroundColor: Style.window.color.warning
        content: RowLayout {
            spacing: 0
            Button {
                Layout.fillWidth: true
                text: "CANCEL"
                onClicked: reject()
            }
            Button {
                Layout.fillWidth: true
                text: "DELETE"
                onClicked: {
                    currentJob.erase();
                    currentProject.jobs.removeJob(currentJob);
                    accept();
                }
            }
        }
    }

    property Component imageSelectionDialog: Dialog {
        id: imageSelectionDialog
        signal imageSelected(string url)
        title: "Select image"
        content: Item {
            ListView {
                anchors.fill: parent
                model: currentJob.images
                clip: true
                spacing: 1
                delegate: ImageDelegate {
                    onImageSelected: {
                        imageSelectionDialog.imageSelected(url);
                        imageSelectionDialog.accept();
                    }
                }
            }
        }
    }
}
