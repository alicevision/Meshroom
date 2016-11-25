import QtQuick 2.7
import QtQuick.Controls 2.0

Label {

    property string shortcut: ""

    anchors.verticalCenter: parent.verticalCenter
    anchors.right: parent.right
    anchors.rightMargin: 5
    text: shortcut
    state: "xsmall"
    enabled: false

    Shortcut {
        sequence: shortcut
        context: Qt.ApplicationShortcut
        onActivated: parent.triggered()
    }
}
