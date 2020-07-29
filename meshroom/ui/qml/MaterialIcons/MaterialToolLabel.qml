import QtQuick 2.9
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3


/**
 * MaterialToolLabel is a Label with an icon (using MaterialIcons).
 * It shows up its tooltip when hovered.
 */
Item {
    id: control
    property alias iconText: icon.text
    property alias iconSize: icon.font.pointSize
    property alias label: labelItem.text
    width: childrenRect.width
    height: childrenRect.height

    RowLayout {
        Label {
            id: icon
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
        Item {
            width: 5
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
