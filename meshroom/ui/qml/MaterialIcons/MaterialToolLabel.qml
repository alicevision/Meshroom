import QtQuick 2.9
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3


/**
 * MaterialToolLabel is a Label with an icon (using MaterialIcons).
 * It shows up its tooltip when hovered.
 */
Item {
    id: control
    property alias iconText: iconItem.text
    property alias iconSize: iconItem.font.pointSize
    property alias label: labelItem.text
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
            color: palette.text
        }
        Label {
            id: labelItem
            text: ""
            color: palette.text
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
