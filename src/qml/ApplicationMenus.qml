import QtQuick 2.7
import QtQuick.Controls 1.4 // using MenuBar

MenuBar {
    id: mainMenu
    Menu {
        title: "File"
        MenuItem {
            text: "New..."
            onTriggered: newScene()
            shortcut: "Ctrl+N"
        }
        MenuSeparator {}
        MenuItem {
            text: "Open..."
            onTriggered: openScene()
            shortcut: "Ctrl+O"
        }
        Menu {
            id: recentSceneMenu
            title: "Open recent..."
            enabled: items.length > 0
            Instantiator {
                model: _application.scenes
                MenuItem {
                    text: model.url.toString().replace("file://", "")
                    onTriggered: openScene(index)
                }
                onObjectAdded: recentSceneMenu.insertItem(index, object)
                onObjectRemoved: recentSceneMenu.removeItem(object)
            }
        }
        MenuSeparator {}
        MenuItem {
            text: "Save"
            onTriggered: saveScene(null)
            enabled: currentScene.dirty
            shortcut: "Ctrl+S"
        }
        MenuItem {
            text: "Save as..."
            onTriggered: saveAsScene(null)
            shortcut: "Ctrl+Shift+S"
        }
    }
    Menu {
        title: "Edit"
        MenuItem {
            text: "Add node..."
            onTriggered: addNode()
            shortcut: "Tab"
        }
        MenuSeparator {}
    }
}
