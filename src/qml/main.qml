import QtQuick 2.7
import QtQuick.Layouts 1.3
import QtQuick.Controls 1.4 // using SplitView
import QtQuick.Controls.Styles 1.4 // using SplitView
import QtQuick.Controls 2.0
import Meshroom.Scene 1.0
import Logger 1.0

import "content"

ApplicationWindow {

    id: _window

    // parameters
    width: 800
    height: 500
    visible: true

    // properties
    property variant currentScene: _application.scene
    property variant defaultScene: Scene {} // used when application is
                                            // about to quit

    // actions
    signal newScene()
    signal openScene()
    signal saveScene(var callback)
    signal saveAsScene(var callback)
    signal addScene(string url)
    signal selectScene(int id)
    signal addNode()
    signal loadAlembic(var file)

    // connections, menus and dialogs
    ApplicationConnections {}
    ApplicationMenus {}
    ApplicationDialogs { id: _dialogs }

    // header
    header: Header {}

    // main content

    property Component scrollViewHandle: Rectangle {
        width: 1; height: 1
        color: (styleData.hovered || styleData.resizing) ? "#5BB1F7" : "#333"
    }

    SplitView {
        anchors.fill: parent
        orientation: Qt.Horizontal
        handleDelegate: scrollViewHandle
        SplitView {
            width: parent.width * 0.75
            height: parent.height
            Layout.minimumWidth: 30
            orientation: Qt.Vertical
            handleDelegate: scrollViewHandle
            ColumnLayout {
                spacing: 0
                width: parent.width
                height: parent.height * 0.55
                TabBar {
                    id: bar
                    TabButton { text: "2D" }
                    TabButton { text: "3D" }
                }
                StackLayout {
                    currentIndex: bar.currentIndex
                    onCurrentIndexChanged: children[currentIndex].focus = true
                    View2D {}
                    View3D {}
                }
            }
            Graph {
                Layout.minimumHeight: 30
                onSelectionChanged: settings.model = node
            }
        }
        Settings {
            id: settings
            Layout.minimumWidth: 30
        }
    }


    // footer
    footer: LogBar {}
}
