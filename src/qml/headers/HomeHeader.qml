import QtQuick 2.2
import QtQuick.Controls 1.3
import QtQuick.Controls.Styles 1.3
import QtQuick.Layouts 1.1
import QtQuick.Dialogs 1.0

import "../components"

Rectangle {

    id : root

    implicitHeight: 30
    color: _style.window.color.darker
    border.color: _style.window.color.xdarker

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 5
        anchors.rightMargin: 5
        spacing: 0
        CustomToolButton {
            iconSource: "qrc:///images/home_outline.svg"
            iconSize: _style.icon.size.small
            text: "home"
        }
    }
}
