import QtQuick 2.2
import QtQuick.Controls 1.3
import QtQuick.Controls.Styles 1.3
import QtQuick.Layouts 1.1
import QtQuick.Dialogs 1.0

import "../components"

Rectangle {

    id: root

    implicitHeight: 30
    color: _style.window.color.xdarker

    Menu {
        id: openMenu
        title: "Open..."
        MenuItem {
            text: "New location..."
            onTriggered: fileDialog.open()
        }
        MenuSeparator {}
        // Menu {
        //     id: recentsMenu
        //     title: "Recents"
        //     enabled: false
        // }
        Menu {
            id: featuredMenu
            title: "Featured"
            enabled: _applicationModel.featuredProjects.length > 0
            Instantiator {
                model: _applicationModel.featuredProjects
                MenuItem {
                    text: modelData
                    onTriggered: _applicationModel.addProject("file://"+modelData)
                }
                onObjectAdded: featuredMenu.insertItem(index, object)
                onObjectRemoved: featuredMenu.removeItem(object)
            }
        }
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 5
        anchors.rightMargin: 5
        spacing: 0
        Item { // spacer
            Layout.fillWidth: true
            Layout.fillHeight: true
        }
        CustomToolButton {
            iconSource: 'qrc:///images/disk.svg'
            iconSize: _style.icon.size.small
            text: "open..."
            onClicked: openMenu.popup()
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
        onAccepted: _applicationModel.addProject(fileDialog.fileUrl)
    }
}
