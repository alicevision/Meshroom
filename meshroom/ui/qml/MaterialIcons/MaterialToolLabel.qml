import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.11


/**
 * MaterialToolLabel is a Label with an icon (using MaterialIcons).
 * It shows up its tooltip when hovered.
 */
Item {
    id: control
    property alias iconText: iconItem.text
    property alias iconSize: iconItem.font.pointSize
    property alias label: labelItem.text
    property var color: palette.text
    implicitWidth: childrenRect.width
    implicitHeight: childrenRect.height
    anchors.rightMargin: 5

    RowLayout {
        Label {
            id: iconItem
            font.family: MaterialIcons.fontFamily
            font.pointSize: 13
            padding: 0
            text: ""
            color: color
        }
        Label {
            id: labelItem
            text: ""
            color: color
        }
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.NoButton
    }
    ToolTip.visible: mouseArea.containsMouse
    ToolTip.delay: 500
}
