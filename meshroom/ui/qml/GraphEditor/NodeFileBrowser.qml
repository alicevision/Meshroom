import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.folderlistmodel

import Controls 1.0
import MaterialIcons 2.2
import Utils 1.0

/**
 * NodeFileBrowser displays the cache folder of a Node as a navigable file browser.
 */
FocusScope {
    id: root

    property variant node: null

    // The root folder URL (node's internal cache folder)
    readonly property url rootFolderUrl: node ? Filepath.stringToUrl(node.internalFolder) : ""
    // Currently displayed folder URL
    property url currentFolder: rootFolderUrl

    // Reset to root folder when node changes
    onRootFolderUrlChanged: {
        root.currentFolder = root.rootFolderUrl
    }

    // Height of a normal (non-hidden) delegate item
    readonly property int itemHeight: 24
    readonly property bool isValidFolder: Filepath.exists(root.currentFolder)

    /**
     * Returns true if the given file name is a Meshroom-internal file that should be hidden,
     * i.e. nodeStatus, chunk log/statistics/status files (e.g. 0.log, 0.statistics, 0.status).
     */
    function isInternalFile(name) {
        return name === "nodeStatus"
            || name.endsWith(".log")
            || name.endsWith(".statistics")
            || name.endsWith(".status")
    }

    SystemPalette { id: activePalette }

    FolderListModel {
        id: folderModel
        folder: root.currentFolder
        showFiles: true
        showDirs: true
        showDirsFirst: true
        showHidden: false
        sortField: FolderListModel.Name
        nameFilters: ["*"]
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // Toolbar: navigate up button, current path label, open-in-OS button
        ToolBar {
            Layout.fillWidth: true

            RowLayout {
                anchors.fill: parent
                spacing: 2

                // Navigate up button
                MaterialToolButton {
                    text: MaterialIcons.arrow_upward
                    font.pointSize: 11
                    padding: 4
                    enabled: root.currentFolder.toString() !== root.rootFolderUrl.toString()
                    ToolTip.text: "Go to parent folder"
                    ToolTip.visible: hovered
                    onClicked: {
                        root.currentFolder = Filepath.stringToUrl(Filepath.dirname(Filepath.urlToString(root.currentFolder)))
                    }
                }

                // Current folder path label
                Label {
                    id: pathLabel
                    Layout.fillWidth: true
                    elide: Text.ElideLeft
                    text: root.node ? Filepath.urlToString(root.currentFolder) : ""
                    ToolTip.text: text
                    ToolTip.visible: hovered && truncated
                    font.pointSize: 8
                    verticalAlignment: Text.AlignVCenter
                }

                // Open current folder in OS file manager
                MaterialToolButton {
                    text: MaterialIcons.folder_open
                    font.pointSize: 11
                    padding: 4
                    enabled: root.node !== null
                    ToolTip.text: "Open folder in file manager"
                    ToolTip.visible: hovered
                    onClicked: Qt.openUrlExternally(root.currentFolder)
                }
            }
        }

        // File list
        ListView {
            id: fileListView
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            focus: true
            // When the folder does not exist, the FolderModel has a fallback to a default folder.
            // We disable the model to avoid this problematic behavior.
            model: isValidFolder ? folderModel : null
            keyNavigationEnabled: true
            highlightFollowsCurrentItem: true

            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

            // Placeholder when folder is empty, does not exist, or contains only internal files
            Label {
                anchors.centerIn: parent
                visible: root.node !== null && fileListView.contentHeight === 0
                color: Qt.lighter(activePalette.mid, 1.2)
                text: isValidFolder ? "Empty folder" : "Folder does not exist"
            }

            delegate: ItemDelegate {
                id: delegateItem
                width: fileListView.width
                // Hide Meshroom-internal files by collapsing their height
                height: root.isInternalFile(fileName) ? 0 : root.itemHeight
                visible: height > 0
                padding: 0
                leftPadding: 6

                // fileIsDir is a FolderListModel role available in the delegate context
                readonly property bool isDir: fileIsDir
                readonly property string itemFilePath: filePath

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 6
                    spacing: 6

                    // File/folder icon
                    MaterialLabel {
                        text: delegateItem.isDir ? MaterialIcons.folder : MaterialIcons.insert_drive_file
                        color: delegateItem.isDir ? "#e8a000" : activePalette.text
                        font.pointSize: 10
                        Layout.alignment: Qt.AlignVCenter
                    }

                    // File/folder name
                    Label {
                        Layout.fillWidth: true
                        // fileName is a FolderListModel role available in the delegate context
                        text: fileName
                        elide: Text.ElideRight
                        font.pointSize: 8
                        verticalAlignment: Text.AlignVCenter
                    }

                    // File size (only for files, fileSize role from FolderListModel)
                    Label {
                        visible: !delegateItem.isDir
                        text: {
                            if (fileSize < 0)
                                return ""
                            if (fileSize < 1024)
                                return fileSize + " B"
                            if (fileSize < 1024 * 1024)
                                return (fileSize / 1024).toFixed(1) + " KB"
                            if (fileSize < 1024 * 1024 * 1024)
                                return (fileSize / (1024 * 1024)).toFixed(1) + " MB"
                            return (fileSize / (1024 * 1024 * 1024)).toFixed(2) + " GB"
                        }
                        color: activePalette.mid
                        font.pointSize: 7
                        rightPadding: 8
                        verticalAlignment: Text.AlignVCenter
                    }
                }

                highlighted: fileListView.currentIndex === index

                onDoubleClicked: {
                    if (delegateItem.isDir) {
                        // fileURL is a FolderListModel role providing the URL
                        root.currentFolder = fileURL
                    } else {
                        Qt.openUrlExternally(fileURL)
                    }
                }
            }
        }
    }
}
