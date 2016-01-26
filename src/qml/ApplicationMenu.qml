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
                enabled: currentProject != null
            }
            MenuItem {
                text: "Open project directory"
                onTriggered: openProjectDirectory()
                enabled: currentProject != null
            }
            // MenuItem {
            //     text: "Add new job"
            //     onTriggered: addJob()
            //     enabled: currentProject != null
            // }
            MenuSeparator {}
            MenuItem {
                text: "Close"
                onTriggered: closeCurrentProject()
                enabled: currentProject != null
            }
        }
        Menu {
            visible: currentProject != null
            title: (currentProject && currentJob) ? "Job: "+truncateText(currentJob.name) : ""
            MenuItem {
                text: "Edit job settings..."
                onTriggered: openJobSettings()
            }
            MenuItem {
                text: "Open job directory"
                onTriggered: openJobDirectory()
                enabled: currentJob ? currentJob.modelData.isValid() : false
            }
            MenuSeparator {}
            MenuItem {
                text: "Duplicate"
            }
            MenuItem {
                text: "Delete"
                onTriggered: deleteJob()
            }
            MenuSeparator {}
            MenuItem {
                text: "Submit..."
                onTriggered: openJobSubmissionDialog()
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
