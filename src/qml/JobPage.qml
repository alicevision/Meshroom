import QtQuick 2.5
import QtQuick.Layouts 1.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import Popart 0.1 // GLView

import "layouts"
import "delegates"
import "headers"
import "components"

TitledPageLayout {

    id : root
    property bool settingsExpanded: false

    signal settingsOpened();
    signal settingsToggled();
    onSettingsOpened: root.settingsExpanded = true
    onSettingsToggled: root.settingsExpanded = !root.settingsExpanded

    header: JobHeader {}
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
            enabled: currentJob.status < 0
            color: _style.window.color.darker
            height: 0
            Behavior on height { NumberAnimation {}}
            Connections { // use this to preserve connection after a manual resize
                target: root
                onSettingsExpandedChanged: settings.height = root.settingsExpanded?180:0
            }
            JobSettingsForm {
                anchors.fill: parent
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
                    enabled: currentJob.status < 0
                    ResourceDropArea {
                        anchors.fill: parent
                        title: "drop .JPG files"
                        onFilesDropped: {
                            for(var i=0; i<files.length; ++i)
                                currentJob.images.addResource(files[i]);
                        }
                        ResourceGallery {
                            id: gallery
                            anchors.fill: parent
                            anchors.margins: 20
                        }
                    }
                }
                Tab {
                    title: "3D"
                    DropArea {
                        anchors.fill: parent
                        onDropped: glview.loadAlembicScene(drop.urls[0])
                        GLView {
                            id: glview
                            property variant job: currentJob
                            onJobChanged: glview.loadAlembicScene(Qt.resolvedUrl(currentJob.url+"/job.abc"))
                            anchors.fill: parent
                            color: "#333"
                        }
                    }
                }
            }
            Rectangle { // vertical tabs
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
