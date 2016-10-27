import QtQuick 2.7
import QtQuick.Controls 1.4 as QQC14
import QtQuick.Controls 2.0

QQC14.MenuBar {
    id: mainMenu
    QQC14.Menu {
        title: "File"
        QQC14.MenuItem {
            text: "New..."
            onTriggered: newScene()
            shortcut: "Ctrl+N"
        }
        QQC14.MenuSeparator {}
        QQC14.MenuItem {
            text: "Open..."
            onTriggered: openScene()
            shortcut: "Ctrl+O"
        }
        QQC14.MenuSeparator {}
        QQC14.MenuItem {
            text: "Save"
            onTriggered: saveScene(null)
            enabled: currentScene.dirty
            shortcut: "Ctrl+S"
        }
        QQC14.MenuItem {
            text: "Save as..."
            onTriggered: saveSceneAs(null)
            shortcut: "Ctrl+Shift+S"
        }
    }
    QQC14.Menu {
        title: "Edit"
        QQC14.MenuItem {
            text: "Add node..."
            onTriggered: addNode()
            shortcut: "Tab"
        }
        QQC14.Menu {
            id: templateMenu
            title: "Import template"
            enabled: items.length > 0
            Instantiator {
                model: _application.templates
                QQC14.MenuItem {
                    text: modelData.name
                    onTriggered: importScene(modelData.url)
                }
                onObjectAdded: templateMenu.insertItem(index, object)
                onObjectRemoved: templateMenu.removeItem(object)
            }
        }
        QQC14.MenuSeparator {}
        QQC14.MenuItem {
            text: "Settings..."
            onTriggered: editSettings()
        }
    }
}
