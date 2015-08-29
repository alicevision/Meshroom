import QtQuick 2.2
import QtQuick.Controls 1.3
import QtQuick.Layouts 1.1
import QtQuick.Dialogs 1.0

import "../components"

Rectangle {

    implicitHeight: 30
    color: _style.window.color.xdarker

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 5
        anchors.rightMargin: 5
        Item { // spacer
            Layout.fillWidth: true
            Layout.fillHeight: true
        }
        CustomToolButton {
            iconSource: 'qrc:///images/disk.svg'
            iconSize: _style.icon.size.small
            text: "filters"
        }
    }
}
