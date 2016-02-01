import QtQuick 2.5
import QtQuick.Controls 1.4
import DarkStyle.Controls 1.0
import DarkStyle 1.0

Item {

    function truncateText(txt) {
        if(txt.length > 15)
            txt = txt.substring(0, 13) + "...";
        return txt;
    }

    Component.onCompleted: _appWindow.menuBar = mainMenu

    MenuBar {
        id: mainMenu
        Menu {
            title: "Project"
            Menu {
                title: "Open..."
                MenuItem {
                    text: "New location..."
                    onTriggered: openProjectDialog()
                }
                MenuSeparator {}
                Menu {
                    id: recentProjectMenu
                    title: "Recents..."
                    enabled: items.length > 0
                }
                Menu {
                    id: featuredProjectMenu
                    title: "Featured..."
                    enabled: items.length > 0
                }
            }
            MenuSeparator {}
            MenuItem {
                text: "Edit project settings..."
                onTriggered: openProjectSettings()
                enabled: currentProject != defaultProject
            }
            MenuItem {
                text: "Open project directory"
                onTriggered: openProjectDirectory()
                enabled: currentProject != defaultProject
            }
            MenuSeparator {}
            MenuItem {
                text: "Close"
                onTriggered: closeCurrentProject()
                enabled: currentProject != defaultProject
            }
        }
        Menu {
            visible: currentProject != defaultProject
            title: "Job: "+truncateText(currentJob.name)
            MenuItem {
                text: "Edit job settings..."
                onTriggered: openJobSettings()
            }
            MenuItem {
                text: "Open job directory"
                onTriggered: openJobDirectory()
                enabled: (currentJob != defaultJob) ? currentJob.isStoredOnDisk() : false
            }
            MenuSeparator {}
            MenuItem {
                text: "Duplicate"
                onTriggered: duplicateJob()
            }
            MenuItem {
                text: "Delete"
                onTriggered: removeJob()
            }
            MenuSeparator {}
            MenuItem {
                text: "Submit..."
                onTriggered: openJobSubmissionDialog()
                enabled: (currentJob != defaultJob) ? currentJob.status < 0 : false
            }
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

    Instantiator {
        model: _applicationModel.featured
        MenuItem {
            text: model.url.toString().replace("file://", "")
            onTriggered: addProject(model.url)
        }
        onObjectAdded: featuredProjectMenu.insertItem(index, object)
        onObjectRemoved: featuredProjectMenu.removeItem(object)
    }

}
