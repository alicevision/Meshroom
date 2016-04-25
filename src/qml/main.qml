import QtQuick 2.5
import QtQuick.Layouts 1.2
import QtQuick.Controls 1.4
import DarkStyle.Controls 1.0
import DarkStyle 1.0
import Meshroom.Scene 1.0

ApplicationWindow {

    id: _window

    // parameters
    width: 800
    height: 500
    visible: true
    color: "#111"
    title: Qt.application.name

    // properties
    property variant currentScene: Scene {}

    // actions
    signal newScene()
    signal openScene()
    signal saveScene(var callback)
    signal saveAsScene(var callback)
    signal addScene(string url)
    signal selectScene(int id)
    signal addNode()

    // main content
    ApplicationConnections {}
    ApplicationMenus {}
    ApplicationDialogs { id: _dialogs }
    ApplicationLayout { anchors.fill: parent }

}
