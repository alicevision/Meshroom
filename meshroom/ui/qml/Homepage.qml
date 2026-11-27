import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Utils 1.0
import MaterialIcons 2.2
import Controls 1.0
import Home 1.0

Page {
    id: root

    property bool isLoading: false
    // Path of the pipeline being loaded ("" for an empty project), undefined when none
    property var loadingPipeline: undefined
    // Index of the selected filter in projectFilters
    property int projectFilter: 0

    // Status filters of the project list (see projectInfo.ProjectStatus): the empty one shows all the projects
    readonly property var projectFilters: [
        { "label": "All projects", "icon": "grid_view", "statuses": [] },
        { "label": "Running or scheduled", "icon": "refresh", "statuses": ["running", "scheduled"] },
        { "label": "Computed", "icon": "check_circle_outline", "statuses": ["computed"] },
        { "label": "Not computed or partial", "icon": "radio_button_unchecked", "statuses": ["notComputed", "partial"] },
        { "label": "Failed", "icon": "error_outline", "statuses": ["failed"] }
    ]
    property bool pipelinesExpanded: true

    function projectMatches(project, filter) {
        return filter["statuses"].length === 0 || filter["statuses"].indexOf(project["info"]["status"]) >= 0
    }

    // Bordered button with an icon and a label: "Empty project", "Open..."
    component HomeButton: Button {
        id: homeButton
        property string iconText: ""
        implicitHeight: 32
        leftPadding: 12
        rightPadding: 12
        hoverEnabled: true
        contentItem: RowLayout {
            spacing: 6
            Label {
                font.family: MaterialIcons.fontFamily
                text: homeButton.iconText
                font.pixelSize: 15
            }
            Label {
                text: homeButton.text
                font.pixelSize: 13
            }
        }
        background: Rectangle {
            radius: 5
            color: homeButton.hovered ? Qt.lighter(palette.button, 1.08) : palette.button
            border.color: palette.mid
        }
    }

    // Title of a section, with a text after it (e.g. the number of items)
    component SectionTitle: RowLayout {
        property alias text: titleLabel.text
        property alias details: detailsLabel.text
        spacing: 8
        Label {
            id: titleLabel
            font.pixelSize: 16
            font.weight: Font.DemiBold
        }
        Label {
            id: detailsLabel
            Layout.alignment: Qt.AlignBaseline
            font.pixelSize: 12
            opacity: 0.6
        }
    }

    // Schedule an action to run after the current frame has been rendered and
    // displayed, so that visual feedback (highlight, spinner) is visible before
    // the UI thread is blocked by a heavy synchronous operation.
    // Uses _window (the ApplicationWindow id from main.qml) since root.window
    // is not reliably available for Page items inside a StackView.
    function executeAfterFrameRendered(action, params = undefined) {
        function onFrame() {
            _window.frameSwapped.disconnect(onFrame)
            if (params === undefined)
                action()
            else
                action(params)
        }
        _window.frameSwapped.connect(onFrame)
    }

    function openProject(path) {
        mainStack.push("Application.qml")
        if (_currentScene.load(path)) {
            MeshroomApp.addRecentProjectFile(path)
        } else {
            root.isLoading = false
            projectsGrid.loadingIndex = -1
        }
    }

    // Create a project from the pipeline template at `path`, an empty project if `path` is empty
    function newProject(path) {
        root.isLoading = true
        root.loadingPipeline = path
        root.executeAfterFrameRendered(function() {
            mainStack.push("Application.qml")
            _currentScene.new(path)
        })
    }

    function openProjectAt(index, path) {
        if (root.isLoading)
            return
        root.isLoading = true
        projectsGrid.loadingIndex = index
        root.executeAfterFrameRendered(openProject, path)
    }

    onVisibleChanged: {
        logo.playing = false
        if (visible) {
            logo.playing = true
            isLoading = false
            loadingPipeline = undefined
            projectsGrid.loadingIndex = -1
        }
    }

    // Read the recent projects again each time the homepage is shown, to show their current status
    StackView.onActivated: MeshroomApp.refreshRecentProjectFiles()

    background: Rectangle { color: palette.window }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        // Sidebar: logo and version, links, sponsors
        Rectangle {
            // Fixed width: the layout must not shrink it when the window is resized
            Layout.preferredWidth: 220
            Layout.minimumWidth: 220
            Layout.maximumWidth: 220
            Layout.fillHeight: true
            color: Qt.darker(palette.window, 1.15)

            Rectangle {
                anchors.right: parent.right
                width: 1
                height: parent.height
                color: Qt.darker(palette.window, 1.6)
            }

            ColumnLayout {
                anchors.fill: parent
                anchors.rightMargin: 1
                spacing: 0

                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: 18 + logo.contentHeight + 6 + versionLabel.implicitHeight + 16
                    color: Colors.meshroomBlue
                    clip: true

                    // The logo and name fill the box (634, 261)-(1284, 806) of the 1920x900 animation:
                    // scale the animation for the box to be 160 px wide, and crop around it
                    AnimatedImage {
                        id: logo
                        readonly property real scale_: 160 / 650
                        readonly property real contentHeight: 545 * scale_
                        width: 1920 * scale_
                        height: 900 * scale_
                        x: parent.width / 2 - 959 * scale_
                        y: 18 - 261 * scale_
                        smooth: true
                        source: "../img/meshroom-anim-once.gif"
                    }
                    Label {
                        id: versionLabel
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: 16
                        anchors.horizontalCenter: parent.horizontalCenter
                        // Without the build details (e.g. the branch)
                        text: Qt.application.version.split(" ")[0]
                        font.pixelSize: 12
                        color: "white"
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.leftMargin: 12
                    Layout.rightMargin: 12
                    Layout.topMargin: 14
                    spacing: 2

                    Repeater {
                        model: [
                            { "label": "Manual", "url": "https://meshroom-manual.readthedocs.io" },
                            { "label": "Release Notes", "url": "https://github.com/alicevision/Meshroom/blob/develop/CHANGES.md" },
                            { "label": "Website", "url": "https://alicevision.org" }
                        ]

                        delegate: ItemDelegate {
                            id: linkDelegate
                            Layout.fillWidth: true
                            implicitHeight: 36
                            leftPadding: 10
                            hoverEnabled: true
                            onClicked: Qt.openUrlExternally(modelData.url)

                            contentItem: RowLayout {
                                spacing: 10
                                Label {
                                    font.family: MaterialIcons.fontFamily
                                    text: MaterialIcons.open_in_new
                                    font.pixelSize: 15
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: modelData.label
                                    font.pixelSize: 15
                                }
                            }
                            background: Rectangle {
                                radius: 5
                                color: linkDelegate.hovered ? palette.window : "transparent"
                            }
                        }
                    }
                }

                Item { Layout.fillHeight: true }

                ColumnLayout {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.topMargin: 18
                    Layout.bottomMargin: 20
                    spacing: 10

                    Label {
                        Layout.alignment: Qt.AlignHCenter
                        text: "Sponsors"
                        font.pixelSize: 12
                        opacity: 0.6
                    }

                    Repeater {
                        model: [
                            [
                                { "image": "MPC.png", "url": "https://www.mpcvfx.com/", "name": "MPC - Moving Picture Company" },
                                { "image": "MILL.png", "url": "https://www.themill.com/", "name": "The Mill" },
                                { "image": "MIKROS.png", "url": "https://www.mikrosanimation.com/", "name": "Mikros Animation" }
                            ],
                            [
                                { "image": "logo_IRIT.png", "url": "https://www.irit.fr/en/departement/dep-hpc-simulation-optimization/reva-team", "name": "IRIT - Institut de Recherche en Informatique de Toulouse" },
                                { "image": "logo_CTU.png", "url": "http://aag.ciirc.cvut.cz", "name": "CTU - Czech Technical University in Prague" },
                                { "image": "logo_uio.png", "url": "https://www.mn.uio.no/ifi/english/about/organisation/dis", "name": "UiO - University of Oslo" },
                                { "image": "logo_enpc.png", "url": "https://imagine-lab.enpc.fr", "name": "ENPC - Ecole des Ponts ParisTech" }
                            ]
                        ]

                        delegate: Row {
                            Layout.alignment: Qt.AlignHCenter
                            spacing: 14

                            Repeater {
                                model: modelData

                                delegate: Image {
                                    source: "../img/" + modelData.image

                                    MouseArea {
                                        anchors.fill: parent
                                        cursorShape: Qt.PointingHandCursor
                                        hoverEnabled: true
                                        onClicked: Qt.openUrlExternally(modelData.url)
                                        ToolTip.visible: containsMouse
                                        ToolTip.text: modelData.name
                                    }
                                }
                            }
                        }
                    }

                    ItemDelegate {
                        id: supportButton
                        Layout.alignment: Qt.AlignHCenter
                        implicitHeight: 32
                        hoverEnabled: true
                        onClicked: Qt.openUrlExternally("https://alicevision.org/association/#donate")

                        contentItem: RowLayout {
                            spacing: 6
                            opacity: supportButton.hovered ? 1.0 : 0.7
                            Label {
                                font.family: MaterialIcons.fontFamily
                                text: MaterialIcons.favorite
                                font.pixelSize: 14
                            }
                            Label {
                                text: "Support AliceVision"
                                font.pixelSize: 12
                            }
                        }
                        background: Item {}
                    }
                }
            }
        }

        ScrollView {
            id: mainView
            Layout.fillWidth: true
            Layout.fillHeight: true
            leftPadding: 32
            rightPadding: 32
            topPadding: 22
            bottomPadding: 48
            contentWidth: availableWidth
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

            ColumnLayout {
                width: mainView.availableWidth
                spacing: 28

                // New project: pipelines by category, collapsible, and empty project
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 14

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 6

                        // Chevron toggling the list of pipelines
                        ItemDelegate {
                            id: pipelinesToggle
                            Layout.leftMargin: -6
                            implicitHeight: 32
                            leftPadding: 4
                            rightPadding: 4
                            hoverEnabled: true
                            onClicked: root.pipelinesExpanded = !root.pipelinesExpanded
                            ToolTip.visible: hovered
                            ToolTip.delay: 500
                            ToolTip.text: root.pipelinesExpanded ? "Hide the pipelines" : "Show the pipelines"

                            contentItem: Label {
                                font.family: MaterialIcons.fontFamily
                                text: MaterialIcons.chevron_right
                                font.pixelSize: 18
                                rotation: root.pipelinesExpanded ? 90 : 0
                                Behavior on rotation { NumberAnimation { duration: 150 } }
                            }
                            background: Rectangle {
                                radius: 4
                                color: pipelinesToggle.hovered ? palette.button : "transparent"
                            }
                        }
                        SectionTitle {
                            text: "New project"
                            details: pipelineList.pipelineCount + (pipelineList.pipelineCount === 1 ? " pipeline" : " pipelines")
                        }
                        Item { Layout.fillWidth: true }
                        BusyIndicator {
                            Layout.preferredWidth: 24
                            Layout.preferredHeight: 24
                            running: root.loadingPipeline === ""
                            visible: running
                        }
                        HomeButton {
                            iconText: MaterialIcons.add
                            text: "Empty project"
                            enabled: !root.isLoading
                            onClicked: root.newProject("")
                        }
                    }

                    PipelineList {
                        id: pipelineList
                        Layout.fillWidth: true
                        visible: root.pipelinesExpanded
                        categories: MeshroomApp.pipelineTemplateCategories
                        loadingPath: root.loadingPipeline
                        onPipelineSelected: function(path) { root.newProject(path) }
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 16

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12

                        SectionTitle {
                            text: "Projects"
                            details: MeshroomApp.recentProjectFiles.length + " total"
                        }

                        // Segmented control filtering the projects by status, with the number of projects of each filter
                        Rectangle {
                            implicitWidth: filtersRow.implicitWidth + 4
                            implicitHeight: filtersRow.implicitHeight + 4
                            radius: 6
                            color: Qt.darker(palette.window, 1.15)
                            border.color: palette.mid

                            RowLayout {
                                id: filtersRow
                                anchors.centerIn: parent
                                spacing: 2

                                Repeater {
                                    model: root.projectFilters

                                    delegate: AbstractButton {
                                        id: filterButton
                                        readonly property bool selected: root.projectFilter === index
                                        readonly property int count: MeshroomApp.recentProjectFiles.filter(p => root.projectMatches(p, modelData)).length

                                        implicitHeight: 28
                                        implicitWidth: filterContent.implicitWidth + 18
                                        hoverEnabled: true
                                        onClicked: root.projectFilter = index

                                        ToolTip.visible: hovered
                                        ToolTip.delay: 300
                                        ToolTip.text: modelData.label + " (" + count + ")"

                                        contentItem: Item {
                                            RowLayout {
                                                id: filterContent
                                                anchors.centerIn: parent
                                                spacing: 5
                                                Label {
                                                    font.family: MaterialIcons.fontFamily
                                                    text: MaterialIcons[modelData.icon]
                                                    font.pixelSize: 15
                                                    color: filterButton.selected ? palette.highlightedText
                                                                                 : (Colors.projectStatusColors[modelData.statuses[0]] || palette.text)
                                                }
                                                Label {
                                                    text: filterButton.count
                                                    font.pixelSize: 12
                                                    color: filterButton.selected ? palette.highlightedText : palette.text
                                                }
                                            }
                                        }
                                        background: Rectangle {
                                            radius: 4
                                            color: filterButton.selected ? palette.highlight : (filterButton.hovered ? palette.button : "transparent")
                                        }
                                    }
                                }
                            }
                        }

                        Item { Layout.fillWidth: true }

                        HomeButton {
                            iconText: MaterialIcons.folder_open
                            text: "Open…"
                            enabled: !root.isLoading
                            ToolTip.visible: hovered
                            ToolTip.delay: 500
                            ToolTip.text: "Open a .mg project (Ctrl+O)"
                            onClicked: {
                                initFileDialogFolder(openFileDialog)
                                openFileDialog.open()
                            }
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        visible: projectsGrid.count === 0
                        implicitHeight: emptyProjectsLabel.implicitHeight + 80
                        radius: 6
                        color: "transparent"
                        border.color: palette.mid

                        Label {
                            id: emptyProjectsLabel
                            anchors.centerIn: parent
                            text: MeshroomApp.recentProjectFiles.length ? "No project matches." : "No recent project."
                            font.pixelSize: 13
                            opacity: 0.6
                        }
                    }

                    GridView {
                        id: projectsGrid
                        Layout.fillWidth: true
                        // Each cell holds a card and the gap on its right: the view is one gap wider than the
                        // content, so that the cards of the last column end on its right edge
                        Layout.rightMargin: -gap
                        // The grid grows with its content: the page scrolls, not the grid
                        Layout.preferredHeight: contentHeight
                        interactive: false

                        property int loadingIndex: -1
                        readonly property int gap: 14
                        // Columns of at least 214 px sharing the width
                        readonly property int columns: Math.max(1, Math.floor(width / (214 + gap)))
                        readonly property real cardWidth: width / columns - gap

                        cellWidth: width / columns
                        cellHeight: Math.round((cardWidth - 2) * 3 / 4) + 2 + 57 + gap

                        model: MeshroomApp.recentProjectFiles.filter(p => root.projectMatches(p, root.projectFilters[root.projectFilter]))

                        // Update grid item when corresponding thumbnail is computed
                        Connections {
                            target: ThumbnailCache
                            function onThumbnailCreated(imgSource, callerID) {
                                let item = projectsGrid.itemAtIndex(callerID)
                                if (item && item.source === imgSource) {
                                    item.updateThumbnail()
                                    return
                                }
                                // fallback in case the item index changed
                                for (let idx = 0; idx < projectsGrid.count; idx++) {
                                    item = projectsGrid.itemAtIndex(idx)
                                    if (item && item.source === imgSource) {
                                        item.updateThumbnail()
                                    }
                                }
                            }
                        }

                        delegate: ProjectCard {
                            width: projectsGrid.cardWidth
                            height: projectsGrid.cellHeight - projectsGrid.gap
                            project: modelData
                            cardIndex: index
                            loading: root.isLoading && index === projectsGrid.loadingIndex
                            opacity: (!root.isLoading || loading) ? 1.0 : 0.4

                            onOpenRequested: root.openProjectAt(index, modelData["path"])
                            onRemoveRequested: MeshroomApp.removeRecentProjectFile(modelData["path"])
                        }
                    }
                }
            }
        }
    }
}
