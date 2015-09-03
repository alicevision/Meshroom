import QtQuick 2.2
import QtQuick.Controls 1.3
import QtQuick.Controls.Styles 1.3
import QtQuick.Layouts 1.1
import QtQuick.Dialogs 1.0

import "../components"

Rectangle {

    id : root
    property variant projectModel: null
    property variant jobModel: null

    signal homeSelected()
    signal projectSelected(int projectID)
    signal projectSettingsToggled()
    signal projectSettingsOpened()
    signal jobRemoved(int projectID, int jobID)

    implicitHeight: 30
    color: _style.window.color.darker
    border.color: _style.window.color.xdarker

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 5
        anchors.rightMargin: 5
        spacing: 0
        CustomToolButton {
            iconSource: "qrc:///images/home_outline.svg"
            iconSize: _style.icon.size.small
            onClicked: homeSelected()
            text: "home"
        }
        CustomToolButton {
            iconSource: "qrc:///images/arrow_right_outline.svg"
            iconSize: _style.icon.size.small
            enabled: false
            opacity: 0.5
        }
        Button {
            text: projectModel.name
            style: ButtonStyle {
                background: Rectangle {
                    color: control.hovered ? _style.window.color.normal : _style.window.color.darker
                    Behavior on color { ColorAnimation{} }
                    border.color: control.hovered ? _style.window.color.xlighter : _style.window.color.lighter
                    radius: 3
                }
                label: CustomText {
                    text: control.text
                    textSize: _style.text.size.small
                    color: _style.text.color.normal
                }
            }
            onClicked: projectSelected(currentProjectID())
        }
        CustomToolButton {
            iconSource: "qrc:///images/arrow_right_outline.svg"
            iconSize: _style.icon.size.small
            enabled: false
            opacity: 0.5
        }
        CustomText {
            text: jobModel.date
            textSize: _style.text.size.small
        }
        Item { // spacer
            Layout.fillWidth: true
        }
        CustomToolButton {
            iconSource: "qrc:///images/gear_outline.svg"
            iconSize: _style.icon.size.small
            onClicked: projectSettingsToggled()
            text: "settings"
        }
        Item { // separator
            Layout.preferredWidth: 20
            Layout.fillHeight: true
            Rectangle {
                anchors.centerIn: parent
                width : 1
                height: parent.height * 0.7
                color: _style.window.color.lighter
            }
        }
        ProgressBar {
            Layout.preferredWidth: (root.jobModel.status >= 0)? 60 : 0
            Behavior on Layout.preferredWidth { NumberAnimation{}}
            value: root.jobModel.completion
            style: ProgressBarStyle {
                background: Rectangle {
                    color: _style.window.color.xdarker
                    implicitWidth: 200
                    implicitHeight: 18
                }
                progress: Rectangle {
                    color: (root.jobModel.status >= 4)? "red" : _style.window.color.selected
                }
            }
        }
        CustomToolButton {
            iconSource: {
                switch(root.jobModel.status) {
                    case 3: // DONE
                    case 0: // BLOCKED
                    case 1: // READY
                    case 2: // RUNNING
                        return "qrc:///images/pause.svg";
                    case 6: // PAUSED
                    case 4: // ERROR
                    case 5: // CANCELED
                    default:
                        return "qrc:///images/play.svg";
                }
            }

            //(root.jobModel.status>=0 )? "qrc:///images/pause.svg" : "qrc:///images/play.svg"
            iconSize: _style.icon.size.small
            onClicked: {
                if(!root.jobModel.save())
                    projectSettingsOpened();
                else
                    root.jobModel.start()
            }
            // highlighted: true
            text: "start"
        }
        CustomToolButton {
            iconSource: "qrc:///images/refresh.svg"
            iconSize: _style.icon.size.small
            text: "refresh"
            onClicked: root.jobModel.refresh()
        }
        Item { // separator
            Layout.preferredWidth: 20
            Layout.fillHeight: true
            Rectangle {
                anchors.centerIn: parent
                width : 1
                height: parent.height * 0.7
                color: _style.window.color.lighter
            }
        }
        CustomToolButton {
            iconSource: "qrc:///images/add_job.svg"
            iconSize: _style.icon.size.small
            onClicked: root.projectModel.addJob()
            text: "duplicate"
        }
        CustomToolButton {
            iconSource: "qrc:///images/trash_outline.svg"
            iconSize: _style.icon.size.small
            onClicked: jobRemoved(currentProjectID(), currentJobID())
            text: "hide"
        }
    }
}
