import QtQuick
import QtQuick.Controls

import MaterialIcons 2.2

/**
 * Shows a busy indicator while @p loading, otherwise a button emitting removeRequested().
 */
Item {
    id: root

    property bool loading: false
    property string toolTip: "Remove"

    signal removeRequested()

    implicitWidth: removeButton.implicitWidth
    implicitHeight: removeButton.implicitHeight

    BusyIndicator {
        anchors.centerIn: parent
        visible: root.loading
        running: visible
        padding: 0
        width: 12
        height: 12
    }

    MaterialToolButton {
        id: removeButton
        anchors.fill: parent
        visible: !root.loading
        text: MaterialIcons.clear
        font.pointSize: 10
        ToolTip.text: root.toolTip
        ToolTip.delay: 500
        onClicked: root.removeRequested()
    }
}
