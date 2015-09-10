import QtQuick 2.2
import QtQuick.Layouts 1.1
import QtQuick.Controls 1.3
import QtQuick.Controls.Styles 1.3

import "layouts"
import "delegates"
import "headers"
import "components"
import Popart 0.1

TitledPageLayout {

    id : root
    property variant projectModel: null
    property variant jobModel: null
    property bool settingsExpanded: true

    header: JobHeader {
        projectModel: root.projectModel
        jobModel: root.jobModel
        onProjectSettingsToggled: root.settingsExpanded = !root.settingsExpanded
        onProjectSettingsOpened: root.settingsExpanded = true
    }
    body: SplitView {
        Layout.fillWidth: true
        Layout.fillHeight: true
        orientation: Qt.Vertical
        handleDelegate: Rectangle {
            width: 2
            height: 2
            color: _style.window.color.xdarker
        }
        Rectangle {
            id: settings
            color: _style.window.color.darker
            height: 180
            Behavior on height { NumberAnimation {}}
            Connections { // use this to preserve connection after manual resize
                target: root
                onSettingsExpandedChanged: settings.height = root.settingsExpanded?180:0
            }
            JobSettingsForm {
                anchors.fill: parent
                jobModel: root.jobModel
            }
            clip: true
        }
        RowLayout {
            Layout.minimumHeight: 50
            Layout.fillHeight: true
            spacing: 0
            TabView {
                id: view
                Layout.fillWidth: true
                Layout.fillHeight: true
                style: TabViewStyle {
                    tab: Item {}
                    frame: Item {}
                }
                Tab {
                    title: "images"
                    ResourceDropArea {
                        anchors.fill: parent
                        function removeResource() {
                            root.jobModel.removeResources(gallery.getSelectionList());
                        }
                        title: "drop .JPG files"
                        enabled: root.jobModel.status < 0
                        onFilesDropped: root.jobModel.addResources(files)
                        ResourceGallery {
                            id: gallery
                            anchors.fill: parent
                            anchors.margins: 20
                            jobModel: root.jobModel
                            enabled: root.jobModel.status < 0
                            Shortcut {
                                key: "Backspace"
                                onActivated: removeResource()
                            }
                            Shortcut {
                                key: "Delete"
                                onActivated: removeResource()
                            }
                        }
                    }
                }
                Tab {
                    title: "3D"
                    DropArea {
                        anchors.fill: parent
                        onDropped: glview.addAlembicScene(drop.urls[0].replace("file://", ""))
                        GLView {
                            id: glview
                            anchors.fill: parent
                            color: "#333"
                        }
                    }
                }
            }
            Rectangle {
                Layout.preferredWidth: 20
                Layout.fillHeight: true
                color: _style.window.color.darker
                ListView {
                    anchors.fill: parent
                    model: view.count
                    spacing: 0
                    delegate: MouseArea {
                        width: parent.width
                        height: childrenRect.height
                        cursorShape: Qt.PointingHandCursor
                        onClicked: view.currentIndex = index
                        Rectangle {
                            color: _style.window.color.normal
                            border.color: _style.window.color.xdarker
                            width: parent.width
                            height: childrenRect.width + 30
                            radius: 5
                            CustomText {
                                text: view.getTab(index).title
                                textSize: _style.text.size.xsmall
                                color: (view.currentIndex==index)?_style.text.color.selected:_style.text.color.normal
                                transform: Rotation { origin.x: 0; origin.y: 15; angle: 90}
                            }
                        }
                    }
                }
            }
        }
    }
}
