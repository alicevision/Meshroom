import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0
import Meshroom.Enums 0.1

Rectangle {

    color: Style.window.color.dark

    function clearOnDestruction() {
        header.clearOnDestruction();
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0
        ToolButton {
            iconSource: "qrc:///images/home.svg"
            text: "home"
            onClicked: closeCurrentProject()
        }
        ToolButton {
            iconSource: "qrc:///images/arrow.svg"
            enabled: false
        }
        Text {
            text: currentProject.name
            font.pixelSize: Style.text.size.small
        }
        ToolButton {
            iconSource: "qrc:///images/arrow.svg"
            enabled: false
        }
        Text {
            text: currentJob.name
            font.pixelSize: Style.text.size.small
        }
        Item { Layout.fillWidth: true } // spacer
        Item { // separator
            Layout.preferredWidth: 10
            Layout.fillHeight: true
            Rectangle {
                anchors.centerIn: parent
                width : 1
                height: parent.height * 0.7
                color: Style.window.color.light
            }
        }
        ProgressBar {
            visible: currentJob.status >= 0
            value: currentJob.completion
            color: {
                switch(currentJob.status) {
                    case Job.PAUSED:
                    case Job.ERROR:
                    case Job.CANCELED:
                    case Job.SYSTEMERROR:
                        return "red";
                    default:
                        return Style.window.color.selected;
                }
            }
        }
        ToolButton {
            visible: currentJob.status < 0
            iconSource: "qrc:///images/play.svg"
            onClicked: openJobSubmissionDialog()
        }
        ToolButton {
            visible: currentJob.status >= 0
            iconSource: "qrc:///images/disk.svg"
            text: "refresh"
            onClicked: refreshJobStatus()
        }
    }

}
