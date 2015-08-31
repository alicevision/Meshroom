import QtQuick 2.2
import QtQuick.Layouts 1.1
import QtQuick.Controls 1.3
import QtQuick.Dialogs 1.0
import QtQuick.Controls.Styles 1.3

import "layouts"
import "headers"
import "components"
import "delegates"

TitledPageLayout {

    id: root
    property variant projectModel: null
    property int labelWidth: 120

    background: DefaultBackground {}
    header: ProjectHeader {
        projectModel: root.projectModel
        onHomeSelected: showHomePage()
    }
    body: Item {
        anchors.fill: parent
        anchors.margins: 20
        ColumnLayout {
            anchors.fill: parent
            spacing: 10
            RowLayout {
                CustomText {
                    Layout.preferredWidth: 80
                    text: "name"
                }
                CustomTextField {
                    Layout.fillWidth: true
                    text: (root.projectModel) ? root.projectModel.name : ""
                    color: (text=="undefined")? "red":"white"
                }
            }
            RowLayout {
                CustomText {
                    Layout.preferredWidth: 80
                    text: "directory"
                }
                RowLayout {
                    CustomTextField {
                        Layout.fillWidth: true
                        text: (root.projectModel) ? root.projectModel.url.toString().replace("file://","") : ""
                        enabled: false
                    }
                    CustomToolButton {
                        iconSource: "qrc:///images/disk.svg"
                        iconSize: _style.icon.size.normal
                    }
                }
            }
            Item { // spacer
                Layout.preferredHeight: 30
            }
            CustomText {
                text: "jobs"
                textSize: _style.text.size.large
                color: _style.text.color.darker
            }
            RowLayout {
                CustomText {
                    Layout.preferredWidth: 80
                    text: "jobs pattern"
                }
                CustomTextField {
                    Layout.fillWidth: true
                    text: "$(project)_$(job)_###"
                }
            }
            RowLayout {
                Item { // spacer
                    // Layout.preferredWidth: 80
                    Layout.fillWidth: true
                }
                CustomToolButton {
                    iconSource: "qrc:///images/add_job.svg"
                    // iconSize: _style.icon.size.small
                    onClicked: root.projectModel.addJob()
                    text: "add job"
                }
                CustomToolButton {
                    iconSource: "qrc:///images/pause_outline.svg"
                    // iconSize: _style.icon.size.small
                    onClicked: root.projectModel.addJob()
                    text: "pause all"
                }
            }
            // RowLayout {
            //     Item {
            //         Layout.preferredWidth: 80
            //     }
            //     CustomTableView {
            //         id: tableView
            //         Layout.fillWidth: true
            //         Layout.preferredHeight: 120
            //         backgroundVisible: false
            //         TableViewColumn {
            //             role: "date"
            //             title: "Job"
            //             // width: tableView.viewport.width * 0.3
            //         }
            //         TableViewColumn {
            //             role: "user"
            //             title: "Author"
            //             width: tableView.viewport.width * 0.2
            //         }
            //         TableViewColumn {
            //             role: "completion"
            //             title: "Completion"
            //             // width: tableView.viewport.width * 0.4
            //         }
            //         model: root.projectModel.jobs
            //         rowDelegate: Rectangle {
            //             height: 30
            //             color: (styleData.row<tableView.rowCount)?(styleData.alternate ? _style.window.color.normal : _style.window.color.darker): "transparent"
            //         }
            //         headerDelegate: Rectangle {
            //             height: 30
            //             color: _style.window.color.xdarker
            //             border.color: _style.window.color.normal
            //             CustomText {
            //                 anchors.centerIn: parent
            //                 text: styleData.value
            //                 textSize: _style.text.size.small
            //             }
            //         }
            //         itemDelegate: Item {
            //             anchors.fill: parent
            //             anchors.leftMargin: 4
            //             anchors.rightMargin: 4
            //             property Component textComponent: CustomText {
            //                 text: styleData.value
            //                 textSize: _style.text.size.small
            //             }
            //             property Component progressComponent: ProgressBar {
            //                 value: styleData.value
            //             }
            //             Loader {
            //                 anchors.verticalCenter: parent.verticalCenter
            //                 sourceComponent: (styleData.column==2)?progressComponent:textComponent
            //             }
            //         }
            //     }
            // }
            Item { // spacer
                Layout.fillHeight: true
            }
        }
    }

    // file dialog
    FileDialog {
        id: fileDialog
        title: "Please choose a project directory"
        folder: "/"
        selectFolder: true
        selectMultiple: false
        sidebarVisible: false
        onAccepted: {
            var newModel = _applicationModel.addNewProject();
            newModel.url = fileDialog.fileUrl;
            newModel.save();
        }
    }

}
