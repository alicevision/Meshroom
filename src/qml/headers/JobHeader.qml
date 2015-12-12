import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.2

import "../components"

Rectangle {

    id : root

    implicitHeight: 30
    color: _style.window.color.darker
    border.color: _style.window.color.xdarker

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 5
        anchors.rightMargin: 5
        spacing: 2
        CustomToolButton {
            iconSource: "qrc:///images/home_outline.svg"
            iconSize: _style.icon.size.small
            enabled: false
            opacity: 0.6
            text: "home"
        }
        CustomToolButton {
            iconSource: "qrc:///images/arrow_right_outline.svg"
            iconSize: _style.icon.size.small
            enabled: false
            opacity: 0.5
        }
        CustomText {
            text: currentProject.name
            textSize: _style.text.size.small
        }
        CustomToolButton {
            iconSource: "qrc:///images/arrow_right_outline.svg"
            iconSize: _style.icon.size.small
            enabled: false
            opacity: 0.5
        }
        CustomText {
            text: currentJob.name
            textSize: _style.text.size.small
        }
        Item { // spacer
            Layout.fillWidth: true
        }
        CustomToolButton {
            iconSource: "qrc:///images/gear_outline.svg"
            iconSize: _style.icon.size.small
            onClicked: settingsToggled()
            text: "settings"
        }
        CustomToolButton {
            visible: currentJob.modelData.isValid()
            iconSource: "qrc:///images/folder_outline.svg"
            iconSize: _style.icon.size.small
            text: "open"
            onClicked: Qt.openUrlExternally(currentJob.url);
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
            iconSource: "qrc:///images/play.svg"
            visible: (currentJob.status<0)
            iconSize: _style.icon.size.small
            onClicked: {
                if(!currentJob.modelData.start())
                    settingsOpened();
            }
            text: "start (farm)"
            CustomText {
                anchors.bottom: parent.bottom
                anchors.right: parent.right
                text: "F"
                textSize: 8
            }
        }
        CustomToolButton {
            iconSource: "qrc:///images/play.svg"
            // visible: (currentJob.status<0)
            iconSize: _style.icon.size.small
            onClicked: {
                if(!currentJob.modelData.start(true))
                    settingsOpened();
            }
            text: "start (local)"
            CustomText {
                anchors.bottom: parent.bottom
                anchors.right: parent.right
                text: "L"
                textSize: 8
            }
        }
        ProgressBar {
            visible: (currentJob.status>=0 && currentJob.status!=3)
            value: currentJob.completion
            style: ProgressBarStyle {
                background: Rectangle {
                    color: _style.window.color.xdarker
                    implicitWidth: 200
                    implicitHeight: 18
                }
                progress: Rectangle {
                    color: {
                        switch(currentJob.status) {
                            case 6: // PAUSED
                                return "yellow";
                            case 4: // ERROR
                                return "red";
                            case 5: // CANCELED
                                return "lightred";
                            case 3: // DONE
                                return "green"
                            case 0: // BLOCKED
                            case 1: // READY
                            case 2: // RUNNING
                            default:
                                return "green"
                        }
                    }
                }
            }
        }
        CustomText {
            visible: (currentJob.status==3)
            text: "DONE"
            color: "green"
            textSize: 12
        }
        CustomToolButton {
            visible: (currentJob.status>=0)
            iconSource: "qrc:///images/refresh.svg"
            iconSize: _style.icon.size.small
            text: "refresh"
            onClicked: currentJob.modelData.refresh()
        }
    }
}
