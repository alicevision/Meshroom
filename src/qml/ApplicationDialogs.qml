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
        content: ColumnLayout {
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
                    id: projectNameCombo
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
                    text: "SAVE"
                    onClicked: {
                        currentProject.name = projectNameCombo.text
                        accept();
                    }
                }
            }
        }
    }

    property Component jobSettingsDialog: Dialog {
        title: "Job settings"
        content: ColumnLayout {
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
                    id: jobNameCombo
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
                    text: "SAVE"
                    onClicked: {
                        currentJob.name = jobNameCombo.text
                        accept();
                    }
                }
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
                        exclusiveGroup: radioGroup
                    }
                    RadioButton {
                        Layout.fillWidth: true
                        text: "Farm"
                        exclusiveGroup: radioGroup
                        checked: true
                    }
                }
                Text {
                    Layout.preferredWidth: 60
                    font.pixelSize: Style.text.size.small
                    horizontalAlignment: Text.AlignRight
                    text: "title :"
                }
                TextField {
                    id: jobNameCombo2
                    Layout.fillWidth: true
                    text: currentJob.name
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
                        currentJob.name = jobNameCombo2.text;
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
        content: ColumnLayout {
            Text {
                Layout.fillWidth: true
                text: "You are about to delete all data associated with this job."
            }
            Text {
                Layout.fillWidth: true
                text: "Are you sure?"
                font.pixelSize: Style.text.size.large
            }
            Item { Layout.fillHeight: true } // spacer
            RowLayout {
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
                        var jobToDelete = currentJob;
                        currentJob = defaultJob;
                        currentProject.jobs.removeJob(jobToDelete);
                        selectJob(currentProject.jobs.count-1);
                        accept();
                    }
                }
            }
        }
    }

    property Component imageSelectionDialog: Dialog {
        id: imageSelectionDialog
        signal imageSelected(string url)
        title: "Select image"
        contentMinimumWidth: 600
        contentMinimumHeight: 500
        content: ColumnLayout {
            RowLayout {
                Text {
                    Layout.fillWidth: true
                    text: currentJob.images.count + " image(s)"
                    font.pixelSize: Style.text.size.small
                    color: Style.text.color.dark
                }
                Button {
                    text: "clear selection"
                    height: 10
                    onClicked: {
                        imageSelectionDialog.imageSelected("");
                        imageSelectionDialog.accept();
                    }
                }
            }
            ListView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                model: currentJob.images
                clip: true
                spacing: 1
                delegate: ImageDelegate {
                    width: parent.width
                    onImageSelected: {
                        imageSelectionDialog.imageSelected(url);
                        imageSelectionDialog.accept();
                    }
                }
            }
        }
    }

    property Component fullscreenImageDialog: Dialog {
        id: fullscreenImageDialog
        property string url: ""
        title: url.toString().replace("file://","")
        contentMinimumWidth: 600
        contentMinimumHeight: 500
        content: Image {
            source: fullscreenImageDialog.url
            fillMode: Image.Tile
            asynchronous: true
        }
    }
}
