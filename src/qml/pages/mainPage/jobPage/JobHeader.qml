import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0

Rectangle {

    color: Style.window.color.dark

    function clearOnDestruction() {
        header.clearOnDestruction();
    }

    Menu {
        id: projectMenu
        MenuItem {
            text: "Edit project name"
            onTriggered: openProjectSettings()
        }
        MenuSeparator {}
        Menu {
            id: recentProjectMenu
            title: "Switch..."
            enabled: items.length > 0
        }
        MenuItem {
            text: "Close"
            onTriggered: closeCurrentProject()
        }
    }
    Menu {
        id: jobMenu
        MenuItem {
            text: "Edit job name"
            onTriggered: openJobSettings()
        }
    }
    Menu {
        id: runMenu
        MenuItem {
            text: "Run locally"
            onTriggered: startJob(true)
        }
        MenuItem {
            text: "Run on farm"
            onTriggered: startJob(false)
        }
    }

    Instantiator {
        model: _applicationModel.projects
        MenuItem {
            text: model.url.toString().replace("file://", "")
            onTriggered: selectProject(index)
        }
        onObjectAdded: recentProjectMenu.insertItem(index, object)
        onObjectRemoved: recentProjectMenu.removeItem(object)
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
        Button {
            text: currentProject.name
            onClicked: projectMenu.popup()
        }
        ToolButton {
            iconSource: "qrc:///images/arrow.svg"
            enabled: false
        }
        Button {
            text: currentJob.name
            onClicked: jobMenu.popup()
        }
        Item { Layout.fillWidth: true } // spacer
        // ToolButton {
        //     visible: currentJob.modelData.isValid()
        //     iconSource: "qrc:///images/disk.svg"
        //     text: "open"
        //     onClicked: openJobDirectory()
        // }
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
            visible: currentJob.status>=0
            value: currentJob.completion
            color: (currentJob.status >= 4)? "red" : Style.window.color.selected
        }
        ToolButton {
            iconSource: "qrc:///images/play.svg"
            onClicked: runMenu.popup()
        }
        ToolButton {
            visible: (currentJob.status>=0)
            iconSource: "qrc:///images/disk.svg"
            text: "refresh"
            onClicked: refreshJobStatus()
        }
    }

}
