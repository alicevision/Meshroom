import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

/**
 * MaterialToolLabel is a Label with an icon (using MaterialIcons).
 * It shows up its tooltip when hovered.
 */

Item {
    id: control
    property alias icon: iconItem
    property alias iconText: iconItem.text
    property alias iconSize: iconItem.font.pointSize
    property alias label: labelItem
    property alias labelIconRow: contentRow
    property var labelIconColor: palette.text
    property alias labelIconMouseArea: mouseArea
    implicitWidth: childrenRect.width
    implicitHeight: childrenRect.height

    RowLayout {
        id: contentRow
        // If we are fitting to a top container, we need to propagate the "anchors.fill: parent"
        // Otherwise, the component defines its own size based on its children.
        anchors.fill: control.anchors.fill ? parent : undefined
        Label {
            id: iconItem
            font.family: MaterialIcons.fontFamily
            font.pointSize: 13
            padding: 0
            text: ""
            color: control.labelIconColor
            Layout.fillWidth: false
            Layout.fillHeight: true
        }
        Label {
            id: labelItem
            text: ""
            color: control.labelIconColor
            Layout.fillWidth: true
            Layout.fillHeight: true
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
