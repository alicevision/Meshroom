import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Dialogs 1.2

import "styles"

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

    // // main loader, needed to enable instant coding
    // Loader {
    //     id: _mainLoader
    //     anchors.fill: parent
    //     objectName: "instanCodingLoader"
    //     source: (_applicationModel.projects.count>0)?"IndexPage.qml":"HomePage.qml"
    // }

    StackView {
        id: stack
        anchors.fill: parent
        property Component indexPage: IndexPage {}
        initialItem: HomePage {}
        Component.onCompleted: {
            if(_applicationModel.projects.count>0)
                stack.push({item:stack.indexPage, immediate: true});
        }
        Connections {
            target: _applicationModel.projects
            onCountChanged: {
                if(_applicationModel.projects.count>0 && stack.depth==1)
                    stack.push({item:stack.indexPage});
                else if(_applicationModel.projects.count==0 && stack.depth>1)
                    stack.pop();
            }
        }
        delegate: StackViewDelegate {
            function transitionFinished(properties) {
                properties.exitItem.opacity = 1;
                _mainWindow.style = _style.bggl;
            }
            pushTransition: StackViewTransition {
                ScriptAction { script: _mainWindow.style = _style.bg; }
                PropertyAnimation {
                    target: enterItem
                    property: "opacity"
                    from: 0
                    to: 1
                }
                PropertyAnimation {
                    target: exitItem
                    property: "opacity"
                    from: 1
                    to: 0
                }
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
        onAccepted: _applicationModel.projects.addProject(fileDialog.fileUrl)
    }
}
