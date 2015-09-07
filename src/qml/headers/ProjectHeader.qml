import QtQuick 2.2
import QtQuick.Controls 1.3
import QtQuick.Controls.Styles 1.3
import QtQuick.Layouts 1.1
import QtQuick.Dialogs 1.0

import "../components"

Rectangle {

    id : root
    property variant projectModel: null

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
            onClicked: selectHomePage()
            text: "home"
        }
        CustomToolButton {
            iconSource: "qrc:///images/arrow_right_outline.svg"
            iconSize: _style.icon.size.small
            enabled: false
            opacity: 0.5
        }
        CustomText {
            text: projectModel.name
            textSize: _style.text.size.small
        }
        Item {
            Layout.fillWidth: true
        }
        // Item { // separator
        //     Layout.preferredWidth: 20
        //     Layout.fillHeight: true
        //     Rectangle {
        //         anchors.centerIn: parent
        //         width : 1
        //         height: parent.height * 0.7
        //         color: _style.window.color.lighter
        //     }
        // }
        CustomToolButton {
            iconSource: "qrc:///images/trash_outline.svg"
            iconSize: _style.icon.size.small
            onClicked: removeProject(projectModel)
            text: "hide"
        }
    }
}
