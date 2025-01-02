import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Utils 1.0
import MaterialIcons 2.2
import Controls 1.0

Page {
    id: root

    onVisibleChanged: {
        logo.playing = false
        if (visible) {
            logo.playing = true
        }
    }

    MSplitView {
        id: splitView
        orientation: Qt.Horizontal
        anchors.fill: parent

        Item {
            SplitView.minimumWidth: 250
            SplitView.preferredWidth: 330
            SplitView.maximumWidth: 500

            ColumnLayout {
                id: leftColumn
                anchors.fill: parent
                spacing: 20

                AnimatedImage {
                    id: logo
                    property var ratio: sourceSize.width / sourceSize.height
                    Layout.fillWidth: true
                    fillMode: Image.PreserveAspectFit
                    // Enforce aspect ratio of the component, as the fillMode does not do the job
                    Layout.preferredHeight: width / ratio
                    smooth: true
                    source: "../img/meshroom-anim-once.gif"
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.margins: 5
                    Layout.leftMargin: 20

                    property real buttonFontSize: 14

                    MaterialToolLabelButton {
                        id: manualButton
                        iconText: MaterialIcons.open_in_new
                        label: "Manual"
                        font.pointSize: parent.buttonFontSize
                        Layout.fillWidth: true
                        onClicked: Qt.openUrlExternally("https://meshroom-manual.readthedocs.io")
                    }

                    MaterialToolLabelButton {
                        id: releaseNotesButton
                        iconText: MaterialIcons.open_in_new
                        label: "Release Notes"
                        font.pointSize: parent.buttonFontSize
                        Layout.fillWidth: true
                        onClicked: Qt.openUrlExternally("https://github.com/alicevision/Meshroom/blob/develop/CHANGES.md")
                    }

                    MaterialToolLabelButton {
                        id: websiteButton
                        iconText: MaterialIcons.open_in_new
                        label: "Website"
                        font.pointSize: parent.buttonFontSize
                        Layout.fillWidth: true
                        onClicked: Qt.openUrlExternally("https://alicevision.org")
                    }
                }

                ColumnLayout {
                    id: sponsors
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignHCenter
                    spacing: 5

                    Item {
                        // Empty area that expands
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                    }

                    Label {
                        Layout.alignment: Qt.AlignHCenter
                        text: "Sponsors"
                    }

                    Image {
                        Layout.alignment: Qt.AlignHCenter
                        source: "../img/technicolor-group_rgb_primary_col-rev.png"

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: Qt.openUrlExternally("https://www.technicolor.com/")

                            hoverEnabled: true
                            ToolTip.visible: containsMouse
                            ToolTip.text: "Technicolor"
                        }
                    }

                    RowLayout {
                        id: brandsRow

                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignHCenter
                        spacing: 20

                        Image {
                            source: "../img/MPC_TG.png"

                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: Qt.openUrlExternally("https://www.mpcvfx.com/")

                                hoverEnabled: true
                                ToolTip.visible: containsMouse
                                ToolTip.text: "MPC - Moving Picture Company"
                            }
                        }

                        Image {
                            source: "../img/MILL_TG.png"

                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: Qt.openUrlExternally("https://www.themill.com/")

                                hoverEnabled: true
                                ToolTip.visible: containsMouse
                                ToolTip.text: "The Mill"
                            }
                        }

                        Image {
                            source: "../img/MIKROS_TG.png"

                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: Qt.openUrlExternally("https://www.mikrosanimation.com/")

                                hoverEnabled: true
                                ToolTip.visible: containsMouse
                                ToolTip.text: "Mikros Animation"
                            }
                        }

                        Image {
                            source: "../img/TechnicolorGames_TG.png"

                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: Qt.openUrlExternally("https://www.technicolorgames.com/")

                                hoverEnabled: true
                                ToolTip.visible: containsMouse
                                ToolTip.text: "Technicolor Games"
                            }
                        }
                    }

                    RowLayout {
                        id: academicRow

                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignHCenter
                        spacing: 28

                        Image {
                            source: "../img/logo_IRIT.png"

                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: Qt.openUrlExternally("https://www.irit.fr/en/departement/dep-hpc-simulation-optimization/reva-team")

                                hoverEnabled: true
                                ToolTip.visible: containsMouse
                                ToolTip.text: "IRIT - Institut de Recherche en Informatique de Toulouse"
                            }
                        }

                        Image {
                            source: "../img/logo_CTU.png"

                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: Qt.openUrlExternally("http://aag.ciirc.cvut.cz")

                                hoverEnabled: true
                                ToolTip.visible: containsMouse
                                ToolTip.text: "CTU - Czech Technical University in Prague"
                            }
                        }

                        Image {
                            source: "../img/logo_uio.png"

                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: Qt.openUrlExternally("https://www.mn.uio.no/ifi/english/about/organisation/dis")

                                hoverEnabled: true
                                ToolTip.visible: containsMouse
                                ToolTip.text: "UiO - University of Oslo"
                            }
                        }

                        Image {
                            source: "../img/logo_enpc.png"

                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: Qt.openUrlExternally("https://imagine-lab.enpc.fr")

                                hoverEnabled: true
                                ToolTip.visible: containsMouse
                                ToolTip.text: "ENPC - Ecole des Ponts ParisTech"
                            }
                        }
                    }

                    MaterialToolLabelButton {
                        Layout.topMargin: 10
                        Layout.bottomMargin: 10
                        Layout.alignment: Qt.AlignHCenter
                        label: "Support AliceVision"
                        iconText: MaterialIcons.favorite

                        // Slightly "extend" the clickable area for the button while preserving the centered layout
                        iconItem.leftPadding: 15
                        labelItem.rightPadding: 15

                        onClicked: Qt.openUrlExternally("https://alicevision.org/association/#donate")
                    }
                }
            }
        }
        
        ColumnLayout {
            id: rightColumn
            SplitView.minimumWidth: 300
            SplitView.fillWidth: true

            TabPanel {
                id: tabPanel
                tabs: ["Pipelines", "Projects"]

                Layout.fillWidth: true
                Layout.fillHeight: true

                ListView {
                    id: pipelinesListView
                    visible: tabPanel.currentTab === 0

                    anchors.fill: parent
                    anchors.margins: 10

                    model: [{ "name": "New Empty Project", "path": null }].concat(MeshroomApp.pipelineTemplateFiles)

                    delegate: Button {
                        id: pipelineDelegate
                        padding: 10
                        width: pipelinesListView.width

                        contentItem: Label {
                            id: pipeline
                            horizontalAlignment: Text.AlignLeft
                            verticalAlignment: Text.AlignVCenter
                            text: modelData["name"]
                        }

                        Connections {
                            target: pipelineDelegate
                            function onClicked() {
                                // Open pipeline
                                mainStack.push("Application.qml")
                                _reconstruction.new(modelData["path"])
                            }
                        }
                    }
                }

                GridView {
                    id: gridView
                    visible: tabPanel.currentTab === 1
                    anchors.fill: parent
                    anchors.topMargin: cellHeight * 0.1

                    cellWidth: 195
                    cellHeight: cellWidth
                    anchors.margins: 10

                    model: {
                        // Request latest thumbnail paths
                        if (mainStack.currentItem instanceof Homepage)
                            MeshroomApp.updateRecentProjectFilesThumbnails()
                        return [{"path": null, "thumbnail": null}].concat(MeshroomApp.recentProjectFiles)
                    }

                    // Update grid item when corresponding thumbnail is computed
                    Connections {
                        target: ThumbnailCache
                        function onThumbnailCreated(imgSource, callerID) {
                            let item = gridView.itemAtIndex(callerID);  // item is an Image
                            if (item && item.source === imgSource) {
                                item.updateThumbnail()
                                return
                            }
                            // fallback in case the Image cellID changed
                            for (let idx = 0; idx < gridView.count; idx++) {
                                item = gridView.itemAtIndex(idx)
                                if (item && item.source === imgSource) {
                                    item.updateThumbnail()
                                }
                            }
                        }
                    }

                    delegate: Column {
                        id: projectContent

                        width: gridView.cellWidth
                        height: gridView.cellHeight

                        property var source: modelData["thumbnail"] ? Filepath.stringToUrl(modelData["thumbnail"]) : ""

                        function updateThumbnail() {
                            thumbnail.source = ThumbnailCache.thumbnail(source, gridView.currentIndex)
                        }

                        onSourceChanged: updateThumbnail()

                        Button {
                            id: projectDelegate
                            height: gridView.cellHeight * 0.95 - project.height
                            width: gridView.cellWidth * 0.9

                            ToolTip.visible: hovered
                            ToolTip.text: modelData["path"] ? modelData["path"] : "Open browser to select a project file"

                            font.family: MaterialIcons.fontFamily
                            font.pointSize: 24

                            text: modelData["path"] ? (modelData["thumbnail"] ? "" : MaterialIcons.description) : MaterialIcons.folder_open

                            Image {
                                id: thumbnail
                                visible: modelData["thumbnail"]
                                cache: false
                                asynchronous: true

                                fillMode: Image.PreserveAspectCrop

                                width: projectDelegate.width
                                height: projectDelegate.height
                            }

                            BusyIndicator {
                                anchors.centerIn: parent
                                running: gridView.visible && modelData["thumbnail"] && thumbnail.status != Image.Ready
                                visible: running
                            }

                            Connections {
                                target: projectDelegate
                                function onClicked() {
                                    if (!modelData["path"]) {
                                        initFileDialogFolder(openFileDialog)
                                        openFileDialog.open()
                                    } else {
                                        // Open project
                                        mainStack.push("Application.qml")
                                        if (_reconstruction.loadUrl(modelData["path"])) {
                                            MeshroomApp.addRecentProjectFile(modelData["path"])
                                        } else {
                                            MeshroomApp.removeRecentProjectFile(modelData["path"])
                                        }
                                    }
                                }
                            }
                        }
                        Label {
                            id: project
                            anchors.horizontalCenter: projectDelegate.horizontalCenter
                            horizontalAlignment: Text.AlignHCenter
                            width: projectDelegate.width
                            elide: Text.ElideMiddle
                            text: modelData["path"] ? Filepath.basename(modelData["path"]) : "Open Project"
                            maximumLineCount: 1
                            font.pointSize: 10
                        }
                    }
                }
            }
        }
    }
}
