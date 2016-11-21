import QtQuick 2.7
import QtQuick.Layouts 1.3
import QtQuick.Controls 2.0
import "controls"

ToolBar {
    RowLayout {
        anchors.fill: parent
        spacing: 10
        RowLayout {
            spacing: 0
            Button {
                text: "File"
                onClicked: fileMenu.open()
                Menu {
                    id: fileMenu
                    y: parent.height
                    MenuItem {
                        text: "New..."
                        onTriggered: newScene()
                        MenuItemShortcut { shortcut: "Ctrl+N" }
                    }
                    MenuItem {
                        text: "Open..."
                        onTriggered: openScene()
                        MenuItemShortcut { shortcut: "Ctrl+O" }
                    }
                    Rectangle { // separator
                        height: 1
                        width: parent.width
                        color: "#333"
                    }
                    MenuItem {
                        text: "Save"
                        onTriggered: saveScene(null)
                        enabled: !currentScene.undoStack.isClean
                        MenuItemShortcut { shortcut: "Ctrl+S" }
                    }
                    MenuItem {
                        text: "Save as..."
                        onTriggered: saveSceneAs(null)
                        MenuItemShortcut { shortcut: "Ctrl+Shift+S" }
                    }
                    Rectangle { // separator
                        height: 1
                        width: parent.width
                        color: "#333"
                    }
                    MenuItem {
                        text: "Quit"
                        MenuItemShortcut { shortcut: "Ctrl+Q" }
                        onTriggered: Qt.quit()
                    }
                }
            }
            Button {
                text: "Edit"
                onClicked: editMenu.open()
                Menu {
                    id: editMenu
                    y: parent.height
                    MenuItem {
                        text: "Undo"
                        onTriggered: currentScene.undoStack.undo()
                        MenuItemShortcut { shortcut: "Ctrl+Z" }
                    }
                    MenuItem {
                        text: "Redo"
                        onTriggered: currentScene.undoStack.redo()
                        MenuItemShortcut { shortcut: "Ctrl+Shift+Z" }
                    }
                    Rectangle { // separator
                        height: 1
                        width: parent.width
                        color: "#333"
                    }
                    MenuItem {
                        text: "Add node..."
                        onTriggered: addNode()
                        MenuItemShortcut { shortcut: "Tab" }
                    }
                    MenuItem {
                        text: "Import template..."
                        onTriggered: importTemplate()
                    }
                    Rectangle { // separator
                        height: 1
                        width: parent.width
                        color: "#333"
                    }
                    MenuItem {
                        text: "Settings..."
                        onTriggered: editSettings()
                        MenuItemShortcut { shortcut: "Ctrl+P" }
                    }
                }
            }
        }
        RowLayout {
            spacing: 0
            Label {
                text: currentScene.name
                state: "xsmall"
            }
            Label {
                text: ".meshroom"
                state: "xsmall"
                enabled: false
            }
            Label {
                text: "*"
                visible: !currentScene.undoStack.isClean
            }
        }
        Item { Layout.fillWidth: true } // spacer
        RowLayout {
            ProgressBar {
                implicitWidth: 100
                implicitHeight: 20
                indeterminate: true
                value: 1
            }
            ToolButton {
                Component.onCompleted: {
                    if(typeof icon == "undefined") return;
                    icon = "qrc:///images/pause.svg"
                }
                text: "STOP"
                onClicked: currentScene.graph.stopWorkerThread()
            }
            visible: currentScene.graph.isRunning
        }
    }
}
