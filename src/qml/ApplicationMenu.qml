import QtQuick 2.5
import QtQuick.Controls 1.4

Item {

    function truncateText(txt) {
        if(txt.length > 15)
            txt = txt.substring(0, 13) + "...";
        return txt;
    }

    MenuBar {
        Menu {
            title: "Project"
            Menu {
                title: "Open..."
                MenuItem {
                    text: "New location..."
                    onTriggered: openProjectLocation()
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
                text: "Edit project settings"
                onTriggered: showProjectSettings()
                enabled: false
            }
            MenuItem {
                text: "Open project directory"
                onTriggered: openProjectDirectory()
            }
            MenuSeparator {}
            MenuItem {
                text: "Add new job"
                onTriggered: addJob()
            }
            MenuItem {
                text: "Remove empty jobs"
                onTriggered: removeEmptyJobs()
                enabled: false
            }
            MenuSeparator {}
            MenuItem {
                text: "Close"
                onTriggered: showHome()
            }
        }
        Menu {
            title: "Job: "+truncateText(currentJob.name)
            MenuItem {
                text: "Edit job settings"
                onTriggered: showJobSettings()
            }
            MenuItem {
                text: "Open job directory"
                onTriggered: openJobDirectory()
            }
            MenuSeparator {}
            MenuItem {
                text: "Run"
                onTriggered: startJob()
            }
        }
    }

    Instantiator {
        model: _applicationModel.projects
        MenuItem {
            text: model.url.toString().replace("file://", "")
            onTriggered: openProject(index)
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
