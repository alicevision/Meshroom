import QtQuick 2.2
import QtQuick.Layouts 1.1
import QtQuick.Controls 1.3

import "../components"

Rectangle {
    color: _style.window.color.darker
    width: parent.width
    height: 30
    MouseArea {
        anchors.fill: parent
        onClicked: _applicationModel.addProject("file://"+modelData)
        RowLayout {
            anchors.fill: parent
            CustomToolButton {
                iconSource: "qrc:///images/project.svg"
                iconSize: _style.icon.size.small
                enabled: false
            }
            Item {
                Layout.fillWidth: true
                CustomWrappedText {
                    anchors.centerIn: parent
                    width: parent.width
                    text: modelData
                }
            }
        }
    }
}
