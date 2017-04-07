import QtQuick 2.7
import QtQuick.Layouts 1.3
import QtQuick.Controls 1.4

MenuBar {

    Menu {
        title: "File"
        MenuItem {
            text: "New..."
            onTriggered: newScene()
            shortcut: "Ctrl+N"
        }
        MenuItem {
            text: "Open..."
            onTriggered: openScene()
            shortcut: "Ctrl+O"
        }
        MenuItem {
            text: "Open recent..."
            onTriggered: openRecentScene()
            enabled: _application.settings.recentFiles.length != 0
        }

        MenuSeparator {}

        MenuItem {
            text: "Save"
            onTriggered: saveScene(null)
            enabled: !currentScene.undoStack.isClean
            shortcut: "Ctrl+S"
        }
        MenuItem {
            text: "Save as..."
            onTriggered: saveSceneAs(null)
            shortcut: "Ctrl+Shift+S"
        }
        MenuSeparator {}
        MenuItem {
            text: "Quit"
            onTriggered: Qt.quit()
            shortcut: "Ctrl+Q"
        }
    }
    Menu {
        title: "Edit"

        MenuItem {
            text: "Undo"
            onTriggered: currentScene.undoStack.undo()
            shortcut: "Ctrl+Z"
        }
        MenuItem {
            text: "Redo"
            onTriggered: currentScene.undoStack.redo()
            shortcut: "Ctrl+Shift+Z"
        }

        MenuSeparator {}

        MenuItem {
            text: "Add node..."
            onTriggered: addNode()
            shortcut: "Tab"
        }

        MenuItem {
            text: "Import template..."
            onTriggered: importTemplate()
        }

        MenuSeparator {}

        MenuItem {
            text: "Settings..."
            onTriggered: editSettings()
            shortcut: "Ctrl+P"
        }

    }
}
