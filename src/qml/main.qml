import QtQuick 2.7
import QtQuick.Layouts 1.3
import QtQuick.Controls 2.0
import Meshroom.Scene 1.0
import Logger 1.0
import "controls"

ApplicationWindow {

    id: _window

    // parameters
    width: 800
    height: 500
    visible: true

    // properties
    property variant currentScene: _application.scene
    property variant currentNode: null
    property variant defaultScene: Scene {} // used when application is
                                            // about to quit

    // actions
    signal newScene()
    signal openScene()
    signal importScene(string url)
    signal saveScene(var callback)
    signal saveSceneAs(var callback)
    signal addScene(string url)
    signal selectScene(int id)
    signal addNode()
    signal loadAlembic(var file)
    signal editSettings()

    // connections, menus and dialogs
    ApplicationConnections {}
    ApplicationMenus {}
    ApplicationDialogs { id: _dialogs }

    // header
    header: Header {}

    SplitView {
        anchors.fill: parent
        orientation: Qt.Horizontal
        initialOffset: 0.75
        minimumSize: 30
        first: SplitView {
            orientation: Qt.Vertical
            initialOffset: 0.5
            minimumSize: 31
            first: ColumnLayout {
                spacing: 0
                TabBar {
                    id: bar
                    TabButton { text: "2D" }
                    TabButton { text: "3D" }
                }
                StackLayout {
                    currentIndex: bar.currentIndex
                    onCurrentIndexChanged: children[currentIndex].focus = true
                    FocusScope {
                        anchors.fill: parent
                        View2D { anchors.fill: parent }
                    }
                    FocusScope {
                        anchors.fill: parent
                        View3D { anchors.fill: parent }
                    }
                }
            }
            second: Graph { onSelectionChanged: currentNode = node }
        }
        second: Settings { model: currentNode }
    }

    // footer
    footer: LogBar {
        expandIcon: expanded ? "qrc:///images/shrink.svg" : "qrc:///images/expand.svg"
        trashIcon: "qrc:///images/trash.svg"
    }

}
