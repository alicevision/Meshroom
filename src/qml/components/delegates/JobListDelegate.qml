import QtQuick 2.2
import QtQuick.Layouts 1.1
import QtQuick.Controls 1.3
import Popart 0.1

import "../../styles"


Item {
    id: root

    property int topItemHeight: 60
    property int subItemHeight: 60
    property bool expanded: false
    property int animationDuration: 300

    width: ListView.view.width
    height: root.topItemHeight + subItemsContainer.height

    Rectangle { // project background
        anchors.fill: parent
        color: "#131313"
        opacity: (root.expanded || topLevelMouse.containsMouse) ? 1 : 0
        Behavior on opacity { NumberAnimation {} }
    }

    Rectangle { // project line separator
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 15
        height: 1
        color: "#424246"
    }

    Column {
        width: parent.width
        height: parent.height

        Item { // top level item
            width: parent.width
            height: root.topItemHeight
            MouseArea {
                id: topLevelMouse
                anchors.fill: parent
                hoverEnabled: true
                onClicked: root.expanded = !root.expanded
            }
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 30
                anchors.rightMargin: 30
                spacing: 15
                ToolButton {
                    style: DefaultStyle.largeToolButton
                    iconSource: root.expanded ? 'qrc:/images/project.svg' : 'qrc:/images/project_outline.svg'
                }
                Item { // project name
                    Layout.fillWidth: false
                    Layout.fillHeight: true
                    Layout.preferredWidth: projectNameText.contentWidth
                    Text {
                        id: projectNameText
                        anchors.verticalCenter: parent.verticalCenter
                        color: "white"
                        elide: Text.ElideRight
                        wrapMode: Text.WrapAnywhere
                        text: root.expanded ? modelData.url : modelData.name
                        maximumLineCount: 1
                        font.pointSize: root.expanded ? 10 : 16
                    }
                }
                Item { // spacer
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                }
                RowLayout {
                    Layout.fillWidth: false
                    Layout.fillHeight: true
                    Layout.preferredWidth: childrenRect.width
                    spacing: 0
                    ToolButton {
                        style: DefaultStyle.smallToolButton
                        tooltip: "add job to project "+modelData.name
                        iconSource: 'qrc:/images/add_job.svg'
                        onClicked: {
                            root.expanded = true;
                            var newModel = modelData.addJob();
                            stackView.push({
                                item: Qt.resolvedUrl("qrc:/pages/NewJobPage.qml"),
                                properties: { model: newModel, projectModel: modelData }});
                        }
                    }
                    ToolButton {
                        style: DefaultStyle.smallToolButton
                        tooltip: "remove project "+modelData.name
                        iconSource: 'qrc:/images/trash_outline.svg'
                        onClicked: _applicationModel.removeProject(modelData)
                    }
                }
            }
        }

        Item { // sub items
            id: subItemsContainer
            width: parent.width
            height: root.expanded ? (jobRepeater.count+0.5) * root.subItemHeight : 0
            clip: true
            Behavior on height {
                SequentialAnimation {
                    NumberAnimation { duration: root.animationDuration; easing.type: Easing.InOutQuad }
                    ScriptAction { script: root.ListView.view.positionViewAtIndex(index, ListView.Contain) }
                }
            }
            Column {
                width: parent.width
                Repeater {
                    id: jobRepeater
                    model: modelData.jobs
                    width: parent.width
                    MouseArea {
                        width: jobRepeater.width
                        height: root.subItemHeight
                        hoverEnabled: true
                        Rectangle { // background
                            anchors.fill: parent
                            color: containsMouse ? "#000" : "transparent"
                            Behavior on color { ColorAnimation {} }
                        }
                        // Timer { // timer
                        //     id: timer
                        //     interval: 10000
                        //     running: modelData.running
                        //     repeat: true
                        //     // triggeredOnStart: true
                        //     onTriggered: modelData.refresh()
                        // }
                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 30
                            anchors.rightMargin: 30
                            spacing: 10
                            Behavior on opacity { NumberAnimation {} }
                            ToolButton {
                                style: DefaultStyle.smallToolButton
                                iconSource: 'qrc:/images/job_outline.svg'
                                enabled: false
                            }
                            Item { // job thumbnail
                                Layout.fillWidth: false
                                Layout.fillHeight: true
                                Layout.preferredWidth: childrenRect.width
                                MouseArea {
                                    id: thumbnailMouseArea
                                    anchors.fill: parent
                                    hoverEnabled: true
                                }
                                Image {
                                    anchors.verticalCenter: parent.verticalCenter
                                    source: (modelData.cameras.length > 0) ? modelData.cameras[0].url : ""
                                    width: parent.height
                                    height: width*3/4.0
                                    asynchronous: true
                                    Rectangle {
                                        width: thumbnailMouseArea.containsMouse ? parent.width : Math.min(cameraCountText.implicitWidth + 15, parent.width)
                                        height: thumbnailMouseArea.containsMouse ? parent.height : cameraCountText.implicitHeight + 5
                                        Behavior on width { NumberAnimation{} }
                                        Behavior on height { NumberAnimation{} }
                                        color: "#99000000"
                                        Text {
                                            id: cameraCountText
                                            anchors.verticalCenter: parent.verticalCenter
                                            width: parent.width
                                            text: modelData.cameras.length
                                            horizontalAlignment: Text.AlignHCenter
                                            color: "white"
                                            font.pointSize: 12
                                            elide: Text.ElideRight
                                            wrapMode: Text.WrapAnywhere
                                            maximumLineCount: 1
                                        }
                                    }
                                }
                            }
                            ProgressBar {
                                Layout.fillWidth: true
                                Layout.minimumWidth: 100
                                Layout.fillHeight: false
                                style: DefaultStyle.progressBar
                                value: modelData.completion
                                enabled: modelData.running
                            }
                            RowLayout {
                                spacing: 0
                                Layout.fillWidth: false
                                Layout.preferredWidth: containsMouse ? 48 : 0
                                opacity: containsMouse ? 1 : 0
                                Behavior on Layout.preferredWidth { NumberAnimation{} }
                                Behavior on opacity { NumberAnimation{} }
                                ToolButton {
                                    style: DefaultStyle.smallToolButton
                                    iconSource: 'qrc:/images/pause_outline.svg'
                                    onClicked: modelData.stop()
                                    visible: modelData.running
                                }
                                ToolButton {
                                    style: DefaultStyle.smallToolButton
                                    iconSource: 'qrc:/images/refresh.svg'
                                    // onClicked: modelData.refresh()
                                }
                            }
                            ToolButton {
                                style: DefaultStyle.labeledToolButton
                                tooltip: "date"
                                text: modelData.date
                            }
                            ToolButton {
                                style: DefaultStyle.labeledToolButton
                                tooltip: "peak threshold"
                                text: modelData.peakThreshold.toFixed(2)
                            }
                            ToolButton {
                                style: DefaultStyle.labeledToolButton
                                tooltip: "meshing scale"
                                text: modelData.meshingScale
                            }
                        }
                    }
                }
            }
        }
    }

}
