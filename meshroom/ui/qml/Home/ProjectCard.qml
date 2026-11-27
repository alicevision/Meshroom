import QtQuick
import QtQuick.Controls
import QtQuick.Effects
import QtQuick.Layouts

import MaterialIcons 2.2
import Utils 1.0

/**
 * Card of a recent project on the homepage: 4:3 thumbnail with the image count, computed nodes, status
 * and progress, then the project name and the pipeline it was created from with its modification date.
 */

Item {
    id: root

    // Entry of MeshroomApp.recentProjectFiles
    property var project: ({})
    // Index of the card in its view, used to match the thumbnails created by the ThumbnailCache
    property int cardIndex: -1
    property bool loading: false
    readonly property var info: project["info"] || {}
    // The project file is read in a thread: its info is empty until then
    readonly property bool reading: info["status"] === undefined
    readonly property string status: info["status"] || "unknown"
    // FileStatus.MISSING until the file is read
    readonly property bool fileExists: reading ? project["status"] !== 0 : status !== "missing"

    property url source: project["thumbnail"] && fileExists ? Filepath.stringToUrl(project["thumbnail"]) : ""
    property int retryCount: 0
    property bool thumbnailBusy: false

    signal openRequested()
    signal removeRequested()

    readonly property var statusLabels: {
        "notComputed": "Not computed",
        "partial": "Partially computed",
        "computed": "Computed",
        "scheduled": "Scheduled",
        "running": "Running",
        "failed": "Failed",
        "unknown": "Unreadable file",
        "missing": "File missing"
    }

    // Status shown on the thumbnail, with the progress of a running computation
    function statusText() {
        if (status === "running")
            return (info["onFarm"] ? "On farm" : "Running") + " · " + Math.floor(info["progress"] * 100) + "%"
        if (status === "scheduled" && info["onFarm"])
            return "Scheduled · Farm"
        return statusLabels[status]
    }

    // Text shown instead of the thumbnail when there is none
    function placeholderText() {
        if (status === "missing")
            return "File not found"
        if (status === "unknown")
            return "Cannot read the file"
        if (status === "failed" && info["failedNode"])
            return "Failed at " + info["failedNode"]
        if (info["totalNodes"] === 0)
            return "Empty graph"
        return info["imageCount"] ? "No preview yet" : "No images yet"
    }

    // Modification date: "Today, 10:42", "Yesterday", "Oct 14" or "Oct 14, 2025"
    function dateText(ms) {
        if (!ms)
            return ""
        const date = new Date(ms)
        const today = new Date()
        const days = Math.round((new Date(today.toDateString()) - new Date(date.toDateString())) / 86400000)
        if (days === 0)
            return "Today, " + Qt.formatTime(date, "hh:mm")
        if (days === 1)
            return "Yesterday"
        return Qt.formatDate(date, date.getFullYear() === today.getFullYear() ? "MMM d" : "MMM d, yyyy")
    }

    function updateThumbnail() {
        thumbnail.source = ThumbnailCache.thumbnail(source, cardIndex)
    }

    onSourceChanged: {
        retryCount = 0
        thumbnailBusy = (source != "")
        updateThumbnail()
    }

    // Chip drawn over the thumbnail, with an icon or a status dot: dark in both palettes
    component Badge: Rectangle {
        id: badge
        property alias text: badgeLabel.text
        property string iconText: ""
        // Color of the status dot, no dot if empty
        property string dotColor: ""
        property bool dotHalf: false
        property bool dotPulse: false
        property bool bold: false

        implicitWidth: badgeRow.implicitWidth + 15
        implicitHeight: badgeRow.implicitHeight + 6
        radius: 4
        color: Qt.rgba(0, 0, 0, 0.75)

        RowLayout {
            id: badgeRow
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.leftMargin: 7
            anchors.rightMargin: 8
            spacing: 5

            Label {

                font.family: MaterialIcons.fontFamily
                visible: badge.iconText !== ""
                text: badge.iconText
                font.pixelSize: 12
                color: "white"
            }
            Rectangle {
                visible: badge.dotColor !== ""
                implicitWidth: 7
                implicitHeight: 7
                radius: 3.5
                color: badge.dotHalf ? "transparent" : badge.dotColor
                border.color: badge.dotColor
                border.width: badge.dotHalf ? 1.5 : 0
                // Left half filled for the partial status
                Rectangle {
                    visible: badge.dotHalf
                    width: parent.width / 2
                    height: parent.height
                    radius: parent.radius
                    color: badge.dotColor
                }
                SequentialAnimation on opacity {
                    running: badge.dotPulse
                    loops: Animation.Infinite
                    alwaysRunToEnd: true
                    NumberAnimation { to: 0.3; duration: 600 }
                    NumberAnimation { to: 1.0; duration: 600 }
                }
            }
            Label {
                id: badgeLabel
                Layout.fillWidth: true
                font.pixelSize: 11
                font.weight: badge.bold ? Font.DemiBold : Font.Normal
                color: "white"
                elide: Text.ElideRight
            }
        }
    }

    // Periodically retry loading the thumbnail until it is available or max retries is reached
    Timer {
        interval: 2000
        repeat: true
        running: root.visible && root.source != ""
                 && thumbnail.status !== Image.Ready
                 && thumbnail.status !== Image.Error
                 && root.retryCount < 15
        onTriggered: {
            root.retryCount++
            if (root.retryCount >= 15)
                root.thumbnailBusy = false
            else
                root.updateThumbnail()
        }
    }

    Rectangle {
        anchors.fill: parent
        radius: 6
        color: mouseArea.containsMouse ? Qt.lighter(palette.button, 1.25) : palette.button
        // Text color at low opacity so that the hover border shows in both themes
        border.color: root.loading ? palette.highlight : mouseArea.containsMouse ? Qt.rgba(palette.text.r, palette.text.g, palette.text.b, 0.45) : palette.mid
        border.width: root.loading ? 2 : 1
        opacity: root.fileExists ? 1.0 : 0.6
        clip: true

        // Thumbnail and overlays
        Rectangle {
            id: preview
            x: 1
            y: 1
            width: parent.width - 2
            height: Math.round(width * 3 / 4)
            color: palette.base

            readonly property bool hasThumbnail: root.source != "" && thumbnail.status === Image.Ready
            // The thumbnail is grey and darker until the project is computed
            readonly property bool dimmed: root.status !== "computed"

            Image {
                id: thumbnail
                anchors.fill: parent
                visible: preview.hasThumbnail && !preview.dimmed
                cache: false
                asynchronous: true
                fillMode: Image.PreserveAspectCrop
                onStatusChanged: {
                    if (status === Image.Ready || status === Image.Error)
                        root.thumbnailBusy = false
                }
            }
            MultiEffect {
                anchors.fill: parent
                source: thumbnail
                visible: preview.hasThumbnail && preview.dimmed
                saturation: -0.85
            }
            // Halves the brightness (MultiEffect.brightness shifts the colors instead of scaling them)
            Rectangle {
                anchors.fill: parent
                visible: preview.hasThumbnail && preview.dimmed
                color: "black"
                opacity: 0.5
            }

            // Placeholder when there is no thumbnail to show
            ColumnLayout {
                anchors.centerIn: parent
                width: parent.width - 24
                visible: !preview.hasThumbnail && !root.thumbnailBusy && !root.reading
                spacing: 10
                opacity: 0.6
                Label {
                    font.family: MaterialIcons.fontFamily
                    Layout.alignment: Qt.AlignHCenter
                    text: MaterialIcons.description
                    font.pixelSize: 30
                }
                Label {
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    text: root.placeholderText()
                    font.pixelSize: 12
                    elide: Text.ElideRight
                }
            }

            BusyIndicator {
                anchors.centerIn: parent
                running: root.thumbnailBusy || root.loading || root.reading
                visible: running
            }

            // Top left: image count and computed nodes
            Column {
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.margins: 8
                spacing: 4

                Badge {
                    visible: root.info["imageCount"] > 0
                    iconText: MaterialIcons.image
                    text: root.info["imageCount"] + (root.info["imageCount"] === 1 ? " image" : " images")
                }
                Badge {
                    visible: root.info["computedNodes"] > 0
                    iconText: MaterialIcons.account_tree
                    text: root.info["computedNodes"] + "/" + root.info["totalNodes"] + " nodes"
                }
            }

            // Bottom left: status
            Badge {
                visible: !root.reading
                anchors.left: parent.left
                anchors.bottom: parent.bottom
                anchors.leftMargin: 8
                anchors.bottomMargin: 9
                width: Math.min(implicitWidth, parent.width - 16)
                bold: true
                dotColor: Colors.projectStatusColors[root.status]
                dotHalf: root.status === "partial"
                dotPulse: root.status === "running"
                text: root.statusText()
            }

            // Bottom edge: progress of a running computation
            Rectangle {
                visible: root.status === "running"
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: 3
                color: Qt.rgba(0, 0, 0, 0.55)
                Rectangle {
                    height: parent.height
                    width: parent.width * (root.info["progress"] || 0)
                    color: Colors.projectStatusColors["running"]
                }
            }
        }

        ColumnLayout {
            anchors.top: preview.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.leftMargin: 12
            anchors.rightMargin: 12
            anchors.topMargin: 9
            spacing: 4

            Label {
                Layout.fillWidth: true
                text: Filepath.basename(root.project["path"])
                font.pixelSize: 13
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 6
                Rectangle {
                    implicitWidth: 7
                    implicitHeight: 7
                    radius: 2
                    color: root.project["pipelineColor"] || "transparent"
                    visible: root.project["pipeline"] !== ""
                }
                Label {
                    Layout.fillWidth: true
                    text: [root.project["pipeline"], root.dateText(root.info["modified"])].filter(Boolean).join(" · ")
                    font.pixelSize: 12
                    opacity: 0.6
                    elide: Text.ElideRight
                }
            }
        }
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        hoverEnabled: true
        cursorShape: root.fileExists ? Qt.PointingHandCursor : Qt.ArrowCursor

        ToolTip.visible: containsMouse
        ToolTip.delay: 500
        ToolTip.text: root.fileExists ? root.project["path"] : root.project["path"] + " — not found"

        onClicked: function(mouse) {
            if (mouse.button === Qt.RightButton) {
                contextMenu.popup()
                return
            }
            if (root.fileExists)
                root.openRequested()
        }
    }

    Menu {
        id: contextMenu

        MenuItem {
            enabled: root.fileExists
            text: "Open"
            onTriggered: root.openRequested()
        }
        MenuItem {
            text: "Copy Path"
            onTriggered: {
                Clipboard.clear()
                Clipboard.setText(root.project["path"])
            }
        }
        MenuItem {
            text: "Remove from List"
            onTriggered: root.removeRequested()
        }
    }
}
