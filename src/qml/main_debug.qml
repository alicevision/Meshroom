import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Dialogs 1.2

import "styles"
import "components"

ApplicationWindow {

    id: _mainWindow

    width: 800
    height: 800
    visible: true
    style: _style.bggl

    menuBar: MenuBar {
        Menu {
            title: "File"
            Menu {
                id: openMenu
                title: "Open..."
                MenuItem {
                    text: "New location..."
                    onTriggered: fileDialog.open()
                }
                MenuSeparator {}
                Instantiator {
                    model: _applicationModel.featured
                    MenuItem {
                        text: model.url.toString().replace("file://", "")
                        onTriggered: _applicationModel.projects.addProject(model.url)
                    }
                    onObjectAdded: openMenu.insertItem(index, object)
                    onObjectRemoved: openMenu.removeItem(object)
                }
            }
        }
    }

    // main application style sheet
    DefaultStyle {
        id: _style
    }

    // main loader, needed to enable instant coding
    Loader {
        id: _mainLoader
        anchors.fill: parent
        objectName: "instanCodingLoader"
        source: (_applicationModel.projects.count>0)?"IndexPage.qml":"HomePage.qml"
    }

    // debug label
    CustomText {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.margins: 2
        text: "debug mode"
        color: "red"
        textSize: _style.text.size.small
    }

    // file dialog
    FileDialog {
        id: fileDialog
        title: "Please choose a project directory"
        folder: "/"
        selectFolder: true
        selectMultiple: false
        sidebarVisible: false
        onAccepted: _applicationModel.projects.addProject(fileDialog.fileUrl)
    }
}
