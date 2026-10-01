import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Controls 1.0

/**
 * Expandable group listing the entries of a LayerList (see LayerRow for the per-entry controls).
 */
ExpandableGroup {
    id: root

    property LayerList layerList: null
    /** Group name; the entry count is appended to build the title. */
    property string name: ""
    property string emptyText: "No entries"
    property bool showPicking: false
    /** Optional per-entry advanced settings; its root item must declare `property var entry`. */
    property Component advancedComponent: null

    readonly property int count: layerList ? layerList.count : 0

    Layout.fillWidth: true
    Layout.fillHeight: true
    title: name + " (" + count + ")"

    Component.onCompleted: expanded = true

    ListView {
        id: listView
        anchors.fill: parent
        visible: root.expanded
        implicitHeight: visible ? Math.min(contentHeight, 220) : 0
        clip: true
        spacing: 4

        ScrollBar.vertical: MScrollBar { id: scrollBar }

        model: root.layerList ? root.layerList.model : null

        delegate: LayerRow {
            width: listView.width - scrollBar.width
            layerList: root.layerList
            showPicking: root.showPicking
            advancedComponent: root.advancedComponent
        }

        Label {
            anchors.centerIn: parent
            visible: root.count === 0
            text: root.emptyText
            color: palette.mid
        }
    }
}
