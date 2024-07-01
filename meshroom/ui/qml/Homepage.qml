import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls 1.4 as Controls1 // For SplitView
import QtQuick.Layouts 1.11
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

    Controls1.SplitView {
        id: splitView
        anchors.fill: parent


        ColumnLayout {
            id: leftColumn
            height: parent.height

            Layout.minimumWidth: 200
            Layout.maximumWidth: 400

            AnimatedImage {
                id: logo
                property var ratio: sourceSize.width / sourceSize.height

                Layout.fillWidth: true
                Layout.preferredHeight: width / ratio

                source: "../img/meshroom-anim-once.gif"
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true

                MaterialToolLabelButton {
                    id: manualButton
                    Layout.topMargin: 20
                    iconText: MaterialIcons.open_in_new
                    label: "Manual"
                    font.pointSize: 16
                    iconSize: 24
                    flat: true
                    leftPadding: 20
                    rightPadding: leftColumn.width - labelItem.width - iconItem.width - leftPadding

                    onClicked: Qt.openUrlExternally("https://meshroom-manual.readthedocs.io/en/latest")
                }

                MaterialToolLabelButton {
                    id: releaseNotesButton
                    iconText: MaterialIcons.open_in_new
                    label: "Release Notes"
                    font.pointSize: 16
                    iconSize: 24
                    flat: true
                    leftPadding: 20
                    rightPadding: leftColumn.width - labelItem.width - iconItem.width - leftPadding

                    onClicked: Qt.openUrlExternally("https://github.com/alicevision/Meshroom/blob/develop/CHANGES.md")
                }

                MaterialToolLabelButton {
                    id: websiteButton
                    iconText: MaterialIcons.open_in_new
                    label: "Website"
                    font.pointSize: 16
                    iconSize: 24
                    flat: true
                    leftPadding: 20
                    rightPadding: leftColumn.width - labelItem.width - iconItem.width - leftPadding

                    onClicked: Qt.openUrlExternally("https://alicevision.org/")
                }
            }

            ColumnLayout {
                id: sponsors
                Layout.fillWidth: true

                Rectangle {
                    // find better alternative
                    color: "transparent"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                }

                Label {
                    Layout.alignment: Qt.AlignHCenter
                    text: "Sponsors"
                    font.pointSize: 16
                }

                Image {
                    Layout.alignment: Qt.AlignHCenter
                    property var ratio: sourceSize.width / sourceSize.height

                    Layout.preferredWidth: leftColumn.width * 0.6
                    Layout.preferredHeight: width / ratio
                    source: "../img/technicolor-group_rgb_primary_col-rev.png"
                    smooth: true
                    mipmap: true

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: Qt.openUrlExternally("https://www.technicolor.com/")
                    }
                }

                RowLayout {
                    id: brandsRow

                    Layout.leftMargin: leftColumn.width * 0.05
                    Layout.rightMargin: leftColumn.width * 0.05

                    Image {
                        property var ratio: sourceSize.width / sourceSize.height

                        Layout.fillWidth: true
                        Layout.preferredHeight: width / ratio
                        source: "../img/MPC_TG.png"
                        smooth: true
                        mipmap: true

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: Qt.openUrlExternally("https://www.mpcvfx.com/")
                        }
                    }

                    Image {
                        property var ratio: sourceSize.width / sourceSize.height

                        Layout.fillWidth: true
                        Layout.preferredHeight: width / ratio
                        source: "../img/MILL_TG.png"
                        smooth: true
                        mipmap: true

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: Qt.openUrlExternally("https://www.themill.com/")
                        }
                    }

                    Image {
                        property var ratio: sourceSize.width / sourceSize.height

                        Layout.fillWidth: true
                        Layout.preferredHeight: width / ratio
                        source: "../img/MIKROS_TG.png"
                        smooth: true
                        mipmap: true

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: Qt.openUrlExternally("https://www.mikrosanimation.com/")
                        }
                    }

                    Image {
                        property var ratio: sourceSize.width / sourceSize.height

                        Layout.fillWidth: true
                        Layout.preferredHeight: width / ratio
                        source: "../img/TechnicolorGames_TG.png"
                        smooth: true
                        mipmap: true

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: Qt.openUrlExternally("https://www.technicolorgames.com/")
                        }
                    }
                }

                MaterialToolLabelButton {
                    Layout.topMargin: 20
                    iconText: MaterialIcons.favorite
                    label: "Support AliceVision"
                    font.pointSize: 16
                    iconSize: 24
                    flat: true

                    leftPadding: (leftColumn.width - labelItem.width - iconItem.width - 5) / 2
                    rightPadding: leftPadding

                    onClicked: Qt.openUrlExternally("https://alicevision.org/association/#donate")
                }
            }
        }
        
        ColumnLayout {
            id: rightColumn

            TabPanel {
                id: tabPanel
                tabs: ["Pipelines", "Recent Projects"]

                font.pointSize: 16

                Layout.fillWidth: true
                Layout.fillHeight: true

                ListView {
                    id: pipelinesListView
                    visible: tabPanel.currentTab === 0

                    anchors.fill: parent

                    model: [{ "name": "New Empty Project", "path": null }].concat(MeshroomApp.pipelineTemplateFiles)

                    delegate: Button {
                        id: pipelineDelegate
                        width: pipelinesListView.width
                        height: pipelineContent.implicitHeight

                        Column {
                            id: pipelineContent
                            topPadding: 8
                            bottomPadding: 10
                            leftPadding: 30

                            Label {
                                id: pipeline
                                text: modelData["name"]
                                font.pointSize: 10
                            }
                        }

                        Connections {
                            target: pipelineDelegate
                            function onClicked() {
                                // Open pipeline
                                mainStack.push("Application.qml")
                                console.log("Open pipeline", modelData["path"])
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

                    cellWidth: 200
                    cellHeight: cellWidth

                    model: MeshroomApp.recentProjectFiles

                    delegate: Column {
                        id: projectContent

                        width: gridView.cellWidth
                        height: gridView.cellHeight
                        Button {
                            id: projectDelegate
                            height: gridView.cellHeight * 0.8
                            width: gridView.cellWidth * 0.8
                            x: gridView.cellWidth * 0.1

                            ToolTip.visible: hovered
                            ToolTip.text: modelData["path"]

                            text: modelData["thumbnail"] ? "" : MaterialIcons.description

                            Image {
                                visible: modelData["thumbnail"]
                                source: modelData["thumbnail"]

                                fillMode: Image.PreserveAspectCrop

                                width: projectDelegate.width
                                height: projectDelegate.height
                            }

                            Connections {
                                target: projectDelegate
                                function onClicked() {
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
                        Label {
                            id: project
                            anchors.horizontalCenter: parent.horizontalCenter
                            horizontalAlignment: Text.AlignHCenter
                            width: projectDelegate.width
                            wrapMode: Text.WrapAnywhere
                            text: {
                                if (Filepath.removeExtension(Filepath.basename(modelData["path"])).length > 40) {
                                    var length = Filepath.basename(modelData["path"]).length
                                    return Filepath.basename(modelData["path"]).substring(0, 30) + "…" + Filepath.basename(modelData["path"]).substring(length - 10, length)
                                } else {
                                    return Filepath.basename(modelData["path"])
                                }
                            }
                            font.pointSize: 10
                        }
                    }
                }
            }
        }
    }
}