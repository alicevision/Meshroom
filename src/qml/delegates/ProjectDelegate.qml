import QtQuick 2.2
import QtQuick.Layouts 1.1
import QtQuick.Controls 1.3
import Popart 0.1

import "../components"

Item {

    id: root

    property int topItemHeight: 60
    property int subItemHeight: 60
    property bool expanded: (index == 0)
    property int animationDuration: 300
    property int projectID: index
    signal projectSelected(int projectID)
    signal jobSelected(int projectID, int jobID)

    width: ListView.view.width
    height: root.topItemHeight + subItemsContainer.height

    Rectangle { // project line separator
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 10
        height: 1
        color: _style.window.color.xlighter
        visible: index != 0
    }

    Column {
        width: parent.width
        height: parent.height

        Item { // top level item
            width: parent.width
            height: root.topItemHeight
            MouseArea {
                id: projectMouseArea
                anchors.fill: parent
                hoverEnabled: true
                onClicked: projectSelected(index)
                onDoubleClicked: root.expanded = !root.expanded
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 15
                    anchors.rightMargin: 10
                    spacing: 5
                    CustomText {
                        text: modelData.name
                        textSize: _style.text.size.large
                        color: (isCurrentProject(projectID)&&currentJobID()==-1)?_style.text.color.selected:_style.text.color.normal
                    }
                    Item { // spacer
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                    }
                    RowLayout {
                        spacing: 0
                        CustomToolButton {
                            iconSource: "qrc:///images/add_job.svg"
                            iconSize: _style.icon.size.small
                            // opacity: root.expanded ? 1 : 0
                            // Behavior on opacity { NumberAnimation {} }
                            text: "add job"
                            onClicked: projectSelected(index)
                        }
                        CustomToolButton {
                            iconSource: "qrc:///images/trash_outline.svg"
                            iconSize: _style.icon.size.small
                            // opacity: root.expanded ? 1 : 0
                            // Behavior on opacity { NumberAnimation {} }
                            text: "hide"
                            onClicked: projectSelected(index)
                        }
                    }
                    CustomToolButton {
                        iconSource: "qrc:///images/arrow_right_outline.svg"
                        iconSize: _style.icon.size.small
                        rotation: root.expanded ? 90 : 0
                        opacity: 0.4
                        Behavior on rotation { NumberAnimation {} }
                        onClicked: root.expanded = !root.expanded
                    }
                }
            }
        }

        Item { // sub items
            id: subItemsContainer
            width: parent.width
            height: root.expanded ? (modelData.jobs.length+0.25) * root.subItemHeight : 0
            clip: true
            Behavior on height {
                SequentialAnimation {
                    NumberAnimation { duration: root.animationDuration; easing.type: Easing.InOutQuad }
                    ScriptAction { script: root.ListView.view.positionViewAtIndex(index, ListView.Contain) }
                }
            }
            ListView {
                id: jobList
                anchors.fill: parent
                model: modelData.jobs
                delegate: JobDelegate {
                    width: parent.width
                    height: root.subItemHeight
                }
                interactive: false
            }
        }
    }

}
