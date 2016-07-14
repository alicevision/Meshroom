import QtQuick 2.5
import QtQuick.Controls 1.4
import DarkStyle.Controls 1.0
import DarkStyle 1.0

Item {

    Component.onCompleted: _applicationWindow.menuBar = mainMenu

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
                onTriggered: closeProject()
                enabled: currentProject != defaultProject
            }
        }
        Menu {
            visible: currentProject != defaultProject
            title: "Job"
            MenuItem {
                text: "Edit job settings..."
                onTriggered: openJobSettings()
                enabled: currentJob.status == -1
            }
            MenuItem {
                text: "Open job directory"
                onTriggered: openJobDirectory()
                shortcut: "Ctrl+J"
                enabled: (currentJob != defaultJob) ? currentJob.status != -1 : false
            }
            MenuSeparator {}
            MenuItem {
                text: "Import images..."
                onTriggered: openImportImageDialog()
                enabled: (currentJob != defaultJob) ? currentJob.status == -1 : false
            }
            MenuSeparator {}
            MenuItem {
                text: "New"
                shortcut: "Ctrl+N"
                onTriggered: addJob()
            }
            MenuItem {
                text: "Duplicate"
                shortcut: "Ctrl+D"
                onTriggered: duplicateJob()
            }
            MenuItem {
                text: "Delete"
                shortcut: "Ctrl+Del"
                onTriggered: removeJob()
            }
            MenuSeparator {}
            MenuItem {
                text: "Submit..."
                shortcut: "Ctrl+S"
                onTriggered: openJobSubmissionDialog()
                enabled: (currentJob != defaultJob) ? currentJob.status == -1 : false
            }
        }
        Menu {
            id: renderMenu
            visible: false
            title: "Rendering"
            MenuItem {
                text: "Show cameras"
                onToggled: showCameras(checked)
                checkable: true
                checked: true
            }
            MenuItem {
                text: "Show gridlines"
                onToggled: showGrid(checked)
                checkable: true
                checked: true
            }
        }
    }

    Connections {
        target: _applicationWindow
        onJobPageTabChanged: {
            renderMenu.visible = (index == 2) // 3d tab
        }
    }

    // instantiators
    Instantiator {
        model: _application.projects
        MenuItem {
            text: model.url.toString().replace("file://", "")
            onTriggered: selectProject(index)
        }
        onObjectAdded: recentProjectMenu.insertItem(index, object)
        onObjectRemoved: recentProjectMenu.removeItem(object)
    }
    Instantiator {
        model: _application.featured
        MenuItem {
            text: model.url.toString().replace("file://", "")
            onTriggered: addProject(model.url)
        }
        onObjectAdded: featuredProjectMenu.insertItem(index, object)
        onObjectRemoved: featuredProjectMenu.removeItem(object)
    }

}
