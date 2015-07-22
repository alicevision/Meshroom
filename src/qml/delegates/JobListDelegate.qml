import QtQuick 2.2
import QtQuick.Layouts 1.1
import QtQuick.Controls 1.3
import Popart 0.1

import "../components"


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
        color: _style.window.color.darker
        opacity: (root.expanded || topLevelMouse.containsMouse) ? 1 : 0
        Behavior on opacity { NumberAnimation {} }
    }

    Rectangle { // project line separator
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 15
        height: 1
        color: "#424246"
        visible: index != 0
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
                CustomToolButton {
                    iconSource: root.expanded ? 'qrc:///images/project.svg' : 'qrc:///images/project_outline.svg'
                }
                CustomText {
                    text: root.expanded ? modelData.url.toString().replace("file://","") : modelData.name
                    textSize: _style.text.size.large
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
                    CustomToolButton {
                        tooltip: "add job to project "+modelData.name
                        iconSource: 'qrc:///images/add_job.svg'
                        onClicked: {
                            root.expanded = true;
                            var newModel = modelData.addJob();
                            stackView.push({
                                item: Qt.resolvedUrl("../pages/NewJobPage.qml"),
                                properties: { model: newModel, projectModel: modelData }});
                        }
                    }
                    CustomToolButton {
                        tooltip: "remove project "+modelData.name
                        iconSource: 'qrc:///images/trash_outline.svg'
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
                            color: containsMouse ? _style.window.color.xdarker : "transparent"
                            Behavior on color { ColorAnimation {} }
                        }
                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 30
                            anchors.rightMargin: 30
                            spacing: 10
                            Behavior on opacity { NumberAnimation {} }
                            CustomToolButton {
                                iconSource: 'qrc:///images/job_outline.svg'
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
                                    // sourceSize.width: parent.height
                                    // sourceSize.height: width*3/4.0
                                    asynchronous: true
                                    Rectangle {
                                        width: thumbnailMouseArea.containsMouse ? parent.width : Math.min(cameraCountText.implicitWidth + 15, parent.width)
                                        height: thumbnailMouseArea.containsMouse ? parent.height : cameraCountText.implicitHeight + 5
                                        Behavior on width { NumberAnimation{} }
                                        Behavior on height { NumberAnimation{} }
                                        color: "#99000000"
                                        CustomText {
                                            id: cameraCountText
                                            text: modelData.cameras.length
                                        }
                                    }
                                }
                            }
                            CustomText {
                                text: modelData.date
                                textSize: _style.text.size.normal
                            }
                            ProgressBar {
                                Layout.fillWidth: true
                                Layout.minimumWidth: 100
                                Layout.fillHeight: false
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
                                CustomToolButton {
                                    iconSource: 'qrc:///images/pause_outline.svg'
                                    onClicked: modelData.stop()
                                    visible: modelData.running
                                }
                                CustomToolButton {
                                    iconSource: 'qrc:///images/refresh.svg'
                                    // onClicked: modelData.refresh()
                                }
                            }
                        }
                    }
                }
            }
        }
    }

}
