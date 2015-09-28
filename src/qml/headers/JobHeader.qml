import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.2

import "../components"

Rectangle {

    id : root

    signal projectSettingsToggled()
    signal projectSettingsOpened()

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
            onClicked: selectHomePage()
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
        CustomToolButton {
            iconSource: "qrc:///images/play.svg"
            visible: (currentJob.status<0)
            iconSize: _style.icon.size.small
            onClicked: {
                if(!currentJob.modelData.save())
                    projectSettingsOpened();
                else
                    currentJob.modelData.start()
            }
            // highlighted: true
            text: "start"
        }
        ProgressBar {
            visible: (currentJob.status>=0)
            value: currentJob.completion
            style: ProgressBarStyle {
                background: Rectangle {
                    color: _style.window.color.xdarker
                    implicitWidth: 200
                    implicitHeight: 18
                }
                progress: Rectangle {
                    color: (currentJob.status >= 4)? "red" : _style.window.color.selected
                }
            }
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
