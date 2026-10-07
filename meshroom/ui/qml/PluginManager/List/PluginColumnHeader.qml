import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import MaterialIcons 2.2

/**
 * Clickable column header for the plugin sortable list.
 */

Item {
    id: root

    property string label: ""
    property string column: ""
    property string sortColumn: ""
    property bool sortAscending: true
    property bool sortable: true

    // Signals
    signal clicked()

    implicitWidth: rowLayout.implicitWidth
    implicitHeight: rowLayout.implicitHeight

    RowLayout {
        id: rowLayout
        anchors.fill: parent
        spacing: 2

        // Column Label
        Label {
            text: root.label
            font.bold: true
            elide: Text.ElideRight
            Layout.fillWidth: true
        }

        // Sort Icon
        Label {
            visible: root.sortable && root.sortColumn === root.column
            text: root.sortAscending ? MaterialIcons.arrow_drop_down : MaterialIcons.arrow_drop_up
            font.family: MaterialIcons.fontFamily
            font.pointSize: 14
            rightPadding: 4
        }

        // Hover Hint
        Label {
            visible: root.sortable && root.sortColumn !== root.column && hoverHandler.hovered
            text: MaterialIcons.filter_list
            font.family: MaterialIcons.fontFamily
            font.pointSize: 10
            rightPadding: 4
            opacity: 0.4
        }
    }

    HoverHandler {
        id: hoverHandler
        enabled: root.sortable
        cursorShape: Qt.PointingHandCursor
    }

    TapHandler {
        enabled: root.sortable
        onTapped: root.clicked()
    }
}
