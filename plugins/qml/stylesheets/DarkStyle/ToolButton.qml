import QtQuick 2.7
import QtQuick.Templates 2.0 as T

import "."

T.ToolButton {

    id: control
    property url icon: ""
    implicitWidth: 30
    implicitHeight: 30
    text: qsTr("ToolButton")
    hoverEnabled: true

    contentItem: Item {
        Label {
            anchors.centerIn: parent
            text: control.text
            font: control.font
            visible: control.icon == ""
        }
    }

    background: Rectangle {
        color: {
            if(control.checked)
                return Globals.window.color.checked;
            if(control.hovered)
                return Qt.darker(Globals.window.color.checked, 1.5)
            return "transparent";
        }
        opacity: 0.8
        Image {
            anchors.fill: parent
            anchors.margins: 1
            visible: control.icon != ""
            source: control.icon
            sourceSize: Qt.size(control.width, control.height)
            asynchronous: true
        }
        MouseArea {
            anchors.fill: parent
            enabled: false
            cursorShape: Qt.PointingHandCursor
        }
    }
}
