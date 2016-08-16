import QtQuick 2.7
import QtQuick.Window 2.2
import QtQuick.Templates 2.0 as T

import "."

T.ApplicationWindow {

    id: window
    visible: true
    title: Qt.application.name
    color: Globals.window.color.xdark

    overlay.modal: Rectangle {
        color: Globals.window.color.xdark
        Behavior on opacity { NumberAnimation { duration: 150 } }
    }
    overlay.modeless: Rectangle {
        color: Globals.window.color.dark
        Behavior on opacity { NumberAnimation { duration: 150 } }
    }

}
