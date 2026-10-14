import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Controls 1.0
import MaterialIcons 2.2

/**
 * CurveList lists the curves of a CurveModel with per curve actions.
 */

ColumnLayout {
    id: root

    spacing: 0

    property var model
    property var viewer
    property real headerHeight: 26

    /// Groups whose curves are hidden in the list, as {group: true}
    property var collapsedGroups: ({})

    function toggleGroup(group) {
        const groups = Object.assign({}, collapsedGroups)
        if (groups[group])
            delete groups[group]
        else
            groups[group] = true
        collapsedGroups = groups
    }

    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: root.headerHeight
        color: palette.window

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 6
            spacing: 0

            Label {
                Layout.fillWidth: true
                text: "Curves (" + (root.model ? root.model.count : 0) + ")"
                elide: Text.ElideRight
            }
            MaterialToolButton {
                text: MaterialIcons.fit_screen
                font.pointSize: 10
                padding: 2
                focusPolicy: Qt.NoFocus
                ToolTip.text: "Fit All Visible Curves (Home)"
                onClicked: root.viewer.fitAll()
            }
            MaterialToolButton {
                text: MaterialIcons.visibility
                font.pointSize: 10
                padding: 2
                focusPolicy: Qt.NoFocus
                ToolTip.text: "Show All Curves (Alt+H)"
                onClicked: root.model.setAllVisible(true)
            }
            MaterialToolButton {
                text: MaterialIcons.visibility_off
                font.pointSize: 10
                padding: 2
                focusPolicy: Qt.NoFocus
                ToolTip.text: "Hide All Curves"
                onClicked: root.model.setAllVisible(false)
            }
            MaterialToolButton {
                text: MaterialIcons.clear
                font.pointSize: 10
                padding: 2
                focusPolicy: Qt.NoFocus
                enabled: root.viewer.rangeEnabled
                ToolTip.text: "Clear Fit Interval (Alt+R)"
                onClicked: root.viewer.rangeEnabled = false
            }
        }

        Rectangle {
            anchors.bottom: parent.bottom
            width: parent.width
            height: 1
            color: palette.shadow
        }
    }

    ListView {
        id: listView

        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        model: root.model
        boundsBehavior: Flickable.StopAtBounds
        keyNavigationEnabled: false

        ScrollBar.vertical: MScrollBar { id: scrollBar }

        delegate: CurveListDelegate {
            // Keep the row buttons out from under the scrollbar
            width: ListView.view.width - (scrollBar.visible ? scrollBar.width : 0)
            curveModel: root.model
            viewer: root.viewer
            collapsed: root.collapsedGroups[curveGroup] === true
        }

        // One header per group (source file), the model keeps the curves of a group contiguous
        section.property: "curveGroup"
        section.delegate: Rectangle {
            id: groupHeader

            required property string section

            width: ListView.view.width - (scrollBar.visible ? scrollBar.width : 0)
            implicitHeight: section ? 24 : 0
            visible: section !== ""
            color: Qt.darker(palette.window, 1.1)

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 4
                spacing: 2

                MaterialLabel {
                    text: root.collapsedGroups[groupHeader.section] ? MaterialIcons.chevron_right : MaterialIcons.expand_more
                    font.pointSize: 11
                }
                Label {
                    Layout.fillWidth: true
                    // Groups are file paths: show the file name
                    text: groupHeader.section.split("/").pop()
                    elide: Text.ElideMiddle
                    font.bold: true
                    ToolTip.text: groupHeader.section
                    ToolTip.visible: headerMouseArea.containsMouse
                    ToolTip.delay: 500
                }
            }

            MouseArea {
                id: headerMouseArea

                anchors.fill: parent
                hoverEnabled: true
                onClicked: root.toggleGroup(groupHeader.section)
            }
        }

        // The current curve is owned by the viewer, ListView.currentIndex is not used
        Connections {
            target: root.viewer
            function onCurrentIndexChanged() {
                if (root.viewer.currentIndex >= 0)
                    listView.positionViewAtIndex(root.viewer.currentIndex, ListView.Contain)
            }
        }
    }
}
