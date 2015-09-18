import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.2
import QtQuick.Dialogs 1.2

import "../components"

Rectangle {

    id: root

    implicitHeight: 30
    color: _style.window.color.xdarker

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 5
        anchors.rightMargin: 5
        spacing: 0
        Item { // spacer
            Layout.fillWidth: true
            Layout.fillHeight: true
        }
        CustomToolButton {
            iconSource: 'qrc:///images/disk.svg'
            iconSize: _style.icon.size.small
            text: "open..."
            onClicked: openMenu.popup()
        }
    }

    // file dialog
    FileDialog {
        id: fileDialog
        title: "Please choose a project directory"
        folder: "/"
        selectFolder: true
        selectMultiple: false
        sidebarVisible: false
        onAccepted: _applicationModel.addProject(fileDialog.fileUrl)
    }
}
