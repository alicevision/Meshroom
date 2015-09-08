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

    background: DefaultBackground {}
    header: HomeHeader {}
    body: Item {
        anchors.fill: parent
        anchors.leftMargin: 30
        anchors.rightMargin: 30
        ColumnLayout {
            anchors.fill: parent
            spacing: 10
            Item { // spacer
                Layout.fillHeight: true
            }
            CustomText {
                text: "Open"
                textSize: _style.text.size.xlarge
                color: _style.text.color.darker
            }
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: Math.min(10, locationView.count+1) * 30
                color: _style.window.color.normal
                ListView {
                    id: locationView
                    anchors.fill: parent
                    anchors.margins: 2
                    spacing: 2
                    clip: true
                    model: _applicationModel.locations
                    delegate: Rectangle {
                        color: _style.window.color.xdarker
                        width: parent.width
                        height: 30
                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                if(index == 0)
                                    fileDialog.open();
                                else
                                    addProject(modelData);
                            }
                            RowLayout {
                                anchors.fill: parent
                                CustomToolButton {
                                    iconSource: (index==0)?"qrc:///images/arrow_right_outline.svg":"qrc:///images/project.svg"
                                    iconSize: _style.icon.size.small
                                    enabled: false
                                }
                                Item {
                                    Layout.fillWidth: true
                                    CustomWrappedText {
                                        anchors.centerIn: parent
                                        width: parent.width
                                        text: modelData
                                    }
                                }
                            }
                        }
                    }
                }
            }
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
        onAccepted: addProject(fileDialog.fileUrl)
    }

}
