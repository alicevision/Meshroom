import QtQuick
import QtCore
import QtQuick.Controls
import QtQuick.Layouts

import Qt.labs.folderlistmodel

import MaterialIcons 2.2
import Utils 1.0

Window {
    id: root
    width: 850
    height: 600
    modality: Qt.ApplicationModal
    flags: Qt.Dialog
    
    property string currentFolder: StandardPaths.writableLocation(StandardPaths.DocumentsLocation)
    property string selectedFile: ""
    property bool saveMode: false // false = Open, true = Save
    property var nameFilters: ["*"]
    property var activePalette: Colors.sysPalette
    
    signal fileSelected(string filePath)
    signal accepted()
    signal rejected()
    
    title: saveMode ? "Save File" : "Open File"

    color: activePalette.base
    
    Settings {
        id: settings
        category: "MeshroomFileDialog"
        property string favorites: ""
        property real sidebarWidth: 200
    }
    
    function loadFavorites() {
        if (settings.favorites) {
            return JSON.parse(settings.favorites)
        }
        return []
    }
    
    function saveFavorites(favs) {
        settings.favorites = JSON.stringify(favs)
    }
    
    function addFavorite(name, path) {
        var favs = loadFavorites()
        // Check if already exists
        for (var i = 0; i < favs.length; i++) {
            if (favs[i].path === path) {
                return // Already in favorites
            }
        }
        favs.push({name: name, path: path})
        saveFavorites(favs)
        favoritesModel.clear()
        loadFavoritesIntoModel()
    }
    
    function removeFavorite(index) {
        var favs = loadFavorites()
        favs.splice(index, 1)
        saveFavorites(favs)
        favoritesModel.clear()
        loadFavoritesIntoModel()
    }
    
    function loadFavoritesIntoModel() {
        var favs = loadFavorites()
        for (var i = 0; i < favs.length; i++) {
            favoritesModel.append(favs[i])
        }
    }
    
    function accept() {
        accepted()
        close()
    }
    
    function reject() {
        rejected()
        close()
    }
    
    function open() {
        show()
        raise()
        requestActivate()
    }

    Component.onCompleted: {
        const currentFilename = _reconstruction.graph.getCurrentFilename()
        selectedFile = _reconstruction.graph.filepath
        filenameField.text = currentFilename
        currentFolder = _reconstruction.graph.getCurrentFolder()
        loadFavoritesIntoModel()
    }
    
    ListModel {
        id: favoritesModel
    }

    component DialogButton: Button {
        flat: true
        property string buttonIcon: MaterialIcons.circle
        property int size: 18
        property color iconColor: root.activePalette.text
        property color backgroundColor:  "transparent"
        property color backgroundColorHovered: root.activePalette.accent
        
        // Icon
        contentItem: Label {
            text: parent.buttonIcon
            font.family: MaterialIcons.fontFamily
            font.pixelSize: parent.size
            color: parent.iconColor
        }
        
        background: Rectangle {
            color: parent.hovered ? parent.backgroundColorHovered : parent.backgroundColor
            radius: 3
        }
    }

    // function filepathExists(path): {
    //     var xhr = new XMLHttpRequest();
    //     xhr.open("HEAD", path, false); // synchronous
    //     try {
    //         xhr.send();
    //         return xhr.status === 200 || xhr.status === 0; // 0 for local files
    //     } catch (e) {
    //         return false;
    //     }
    // }
    
    // Custom title bar
    // Could be used to add options and menus
    // For now only the name of the mode (Opn/Save and a close UI button)
    Rectangle {
        id: titleBar
        width: parent.width
        height: 40
        color: Qt.lighter(root.activePalette.base, 1.4)
        z: 100
        
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 15
            anchors.rightMargin: 10
            spacing: 10
            
            Label {
                text: root.title
                font.bold: true
                font.pixelSize: 13
                color: root.activePalette.text
                Layout.fillWidth: true
            }
            
            DialogButton {
                buttonIcon: MaterialIcons.close
                ToolTip.text: "Close"
                onClicked: root.reject()
            }
        }
    }
    
    RowLayout {
        anchors.fill: parent
        anchors.topMargin: 40
        spacing: 0
        
        // LEFT SIDEBAR
        Rectangle {
            id: sidebar
            Layout.fillHeight: true
            Layout.preferredWidth: settings.sidebarWidth
            Layout.minimumWidth: 150
            Layout.maximumWidth: 400
            color: Qt.darker(root.activePalette.base, 1.4)
            
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 8
                
                // System folders
                Label {
                    text: "System"
                    font.bold: true
                    font.pixelSize: 11
                    color: Qt.darker(root.activePalette.text, 1.4)
                }
                
                Repeater {
                    model: [
                        {
                            name: "Home", 
                            icon: MaterialIcons.home, 
                            path: StandardPaths.writableLocation(StandardPaths.HomeLocation)
                        },
                        {
                            name: "Desktop", 
                            icon: MaterialIcons.desktop_windows, 
                            path: StandardPaths.writableLocation(StandardPaths.DesktopLocation)
                        },
                        {
                            name: "Documents", 
                            icon: MaterialIcons.description, 
                            path: StandardPaths.writableLocation(StandardPaths.DocumentsLocation)
                        },
                        {
                            name: "Downloads", 
                            icon: MaterialIcons.download, 
                            path: StandardPaths.writableLocation(StandardPaths.DownloadLocation)
                        },
                        {
                            name: "Pictures", 
                            icon: MaterialIcons.image, 
                            path: StandardPaths.writableLocation(StandardPaths.PicturesLocation)
                        }
                    ]

                    Button {
                        Layout.fillWidth: true
                        flat: true
                        
                        contentItem: RowLayout {
                            spacing: 8
                            Label {
                                text: modelData.icon
                                font.family: MaterialIcons.fontFamily
                                font.pixelSize: 18
                                color: root.activePalette.text
                            }
                            Label {
                                text: modelData.name
                                color: root.activePalette.text
                                Layout.fillWidth: true
                            }
                        }
                        
                        background: Rectangle {
                            color: parent.hovered ? root.activePalette.accent : "transparent"
                            radius: 3
                        }
                        onClicked: folderModel.customFolder = modelData.path
                    }
                }
                
                // Separator
                Rectangle {
                    Layout.fillWidth: true
                    height: 1
                    color: Qt.lighter(root.activePalette.base, 1.4)
                    Layout.topMargin: 8
                    Layout.bottomMargin: 8
                }
                
                // Favorites section
                RowLayout {
                    Layout.fillWidth: true
                    
                    Label {
                        text: "Favorites"
                        font.bold: true
                        font.pixelSize: 11
                        color: Qt.darker(root.activePalette.text, 1.4)
                        Layout.fillWidth: true
                    }

                    DialogButton {
                        buttonIcon: MaterialIcons.add
                        onClicked: {
                            var path = folderModel.folder.toString().replace("file://", "")
                            var name = path.split("/").pop() || "Root"
                            addFavorite(name, path)
                        }
                    }
                }
                
                // Drop area for favorites
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: favDropArea.containsDrag ? root.activePalette.base : "transparent"
                    border.color: favDropArea.containsDrag ? root.activePalette.accent : "transparent"
                    border.width: 2
                    radius: 3
                    
                    DropArea {
                        id: favDropArea
                        anchors.fill: parent
                        
                        onDropped: (drop) => {
                            if (drop.hasUrls) {
                                for (var i = 0; i < drop.urls.length; i++) {
                                    var url = drop.urls[i].toString()
                                    var path = url.replace("file://", "")
                                    var name = path.split("/").pop()
                                    addFavorite(name, path)
                                }
                            }
                        }
                    }
                    
                    ScrollView {
                        anchors.fill: parent
                        clip: true
                        
                        ListView {
                            id: favoritesListView
                            model: favoritesModel
                            spacing: 2
                            
                            delegate: Button {
                                width: ListView.view.width
                                flat: true
                                
                                contentItem: RowLayout {
                                    spacing: 5
                                    
                                    Label {
                                        text: MaterialIcons.star
                                        font.family: MaterialIcons.fontFamily
                                        font.pixelSize: 16
                                        color: root.activePalette.text
                                    }
                                    
                                    Label {
                                        text: model.name
                                        color: root.activePalette.text
                                        elide: Text.ElideRight
                                        Layout.fillWidth: true
                                    }
                                    
                                    DialogButton {
                                        buttonIcon: MaterialIcons.close
                                        backgroundColorHovered: Qt.darker(Colors.red, 1.4)
                                        onClicked: removeFavorite(model.index)
                                    }
                                }
                                
                                background: Rectangle {
                                    color: parent.hovered ? root.activePalette.accent : "transparent"
                                    radius: 3
                                }
                                
                                onClicked: folderModel.customFolder = model.path
                            }
                        }
                    }
                    
                    Label {
                        anchors.centerIn: parent
                        text: "Drop folders here"
                        color: Colors.grey
                        visible: favoritesModel.count === 0 && !favDropArea.containsDrag
                        font.pixelSize: 11
                    }
                }
            }
        }
        
        // Resize left section
        Rectangle {
            Layout.fillHeight: true
            width: 4
            color: resizeArea.containsMouse ? root.activePalette.accent : Qt.lighter(root.activePalette.base, 1.4)
            
            MouseArea {
                id: resizeArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.SizeHorCursor
                
                property real startX: 0
                property real startWidth: 0
                
                onPressed: (mouse) => {
                    startX = mouse.x
                    startWidth = sidebar.Layout.preferredWidth
                }
                
                onPositionChanged: (mouse) => {
                    if (pressed) {
                        var delta = mouse.x - startX
                        var newWidth = startWidth + delta
                        if (newWidth >= sidebar.Layout.minimumWidth && newWidth <= sidebar.Layout.maximumWidth) {
                            sidebar.Layout.preferredWidth = newWidth
                            settings.sidebarWidth = newWidth
                        }
                    }
                }
            }
        }
        
        // Right section
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0
            
            // Toolbar with search bar
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 50
                color: Qt.lighter(root.activePalette.base, 1.4)
                
                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 8
                    spacing: 8
                    
                    DialogButton {
                        buttonIcon: MaterialIcons.arrow_upward
                        ToolTip.text: "Go up one level"
                        onClicked: {
                            var url = folderModel.folder.toString()
                            var parentPath = url.substring(0, url.lastIndexOf("/"))
                            if (parentPath.length > 7) // more than "file://"
                                folderModel.customFolder = parentPath
                        }
                    }
                    
                    TextField {
                        id: pathField
                        Layout.fillWidth: true
                        text: folderModel.folder.toString().replace("file://", "")
                        selectByMouse: true
                        color: root.activePalette.text
                        background: Rectangle {
                            color: root.activePalette.base
                            border.color: pathField.activeFocus ? root.activePalette.accent : Qt.darker(root.activePalette.base, 1.4)
                            border.width: 1
                            radius: 3
                        }
                        onAccepted: folderModel.customFolder = text
                    }
                    
                    DialogButton {
                        buttonIcon: MaterialIcons.refresh
                        ToolTip.text: "Refresh"
                        onClicked: {
                            var temp = folderModel.folder
                            folderModel.folder = ""
                            folderModel.folder = temp
                        }
                    }
                }
            }
            
            // File list header
            Rectangle {
                Layout.fillWidth: true
                height: 30
                color: root.activePalette.base
                
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 10
                    spacing: 10
                    
                    Label { 
                        text: "Name"
                        Layout.fillWidth: true
                        font.bold: true
                        color: Qt.darker(root.activePalette.text, 1.4)
                    }

                    Label {
                        text: "Date Modified"
                        Layout.preferredWidth: 150
                        font.bold: true
                        color: Qt.darker(root.activePalette.text, 1.4)
                    }

                    Label {
                        text: "Size"
                        Layout.preferredWidth: 80
                        font.bold: true
                        color: Qt.darker(root.activePalette.text, 1.4)
                    }
                }
            }
            
            // File list view
            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                
                ListView {
                    id: fileListView
                    clip: true
                    
                    model: FolderListModel {
                        id: folderModel
                        showDirs: true
                        showDirsFirst: true
                        nameFilters: root.nameFilters

                        property string customFolder: ""
                        onCustomFolderChanged: {
                            if (customFolder != "")
                                folder = customFolder.startsWith("file://") ? customFolder : "file://" + customFolder
                        }

                        Component.onCompleted: {
                            customFolder = root.currentFolder
                        }
                    }
                    
                    delegate: ItemDelegate {
                        width: ListView.view.width
                        height: 35

                        function isCurrentItemSelected() {
                            const currentModelFile = model.fileURL.toString().replace("file://", "")
                            if (currentModelFile === root.selectedFile) {
                                fileListView.currentIndex = model.index
                                return true
                            }
                            return false
                        }

                        highlighted: fileListView.currentIndex == -1 ? isCurrentItemSelected() : ListView.isCurrentItem


                        // Enable drag for folders
                        property bool isDragging: false
                        Drag.active: isDragging
                        Drag.dragType: Drag.Automatic
                        Drag.supportedActions: Qt.CopyAction
                        Drag.mimeData: { "text/uri-list": model.fileURL.toString() }
                        
                        background: Rectangle {
                            color: highlighted ? root.activePalette.accent : (model.index % 2 ? root.activePalette.base : Qt.darker(root.activePalette.base, 1.2))
                        }
                        
                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 10
                            spacing: 10
                            
                            Label {
                                text: model.fileIsDir ? MaterialIcons.folder : MaterialIcons.insert_drive_file
                                font.family: MaterialIcons.fontFamily
                                font.pixelSize: 18
                                color: Colors.getFileColor(model.fileIsDir ? "" : model.fileName)
                            }
                            
                            Label {
                                text: model.fileName
                                Layout.fillWidth: true
                                elide: Text.ElideRight
                                color: root.activePalette.text
                            }
                            
                            Label {
                                text: Qt.formatDateTime(model.fileModified, "dd MMM yyyy hh:mm")
                                Layout.preferredWidth: 150
                                color: Qt.darker(root.activePalette.text, 1.2)
                                font.pixelSize: 11
                            }
                            
                            Label {
                                text: model.fileIsDir ? "" : (model.fileSize / 1024).toFixed(1) + " KB"
                                Layout.preferredWidth: 80
                                color: Qt.darker(root.activePalette.text, 1.2)
                                font.pixelSize: 11
                            }
                        }
                        
                        MouseArea {
                            anchors.fill: parent
                            drag.target: model.fileIsDir ? parent : null

                            onPressed: {
                                if (model.fileIsDir) {
                                    parent.isDragging = true
                                }
                            }

                            onReleased: {
                                parent.isDragging = false
                            }

                            onClicked: {
                                fileListView.currentIndex = model.index
                                if (model.fileIsDir) {
                                    if (!saveMode) {
                                        filenameField.text = ""
                                    }
                                } else {
                                    filenameField.text = model.fileName
                                }
                            }
                            
                            onDoubleClicked: {
                                if (model.fileIsDir) {
                                    folderModel.folder = model.fileURL
                                } else {
                                    if (!saveMode) {
                                        root.selectedFile = model.fileURL.toString()
                                        root.fileSelected(selectedFile)
                                        root.accept()
                                    }
                                }
                            }
                        }
                    }
                }
            }
            
            // File selection bar
            Rectangle {
                id: selectionBar

                Layout.fillWidth: true
                Layout.preferredHeight: 60
                color: Qt.lighter(root.activePalette.base, 1.4)

                function getSelectedPath() {
                    return folderModel.folder.toString().replace("file://", "") + "/" + filenameField.text
                }

                function selectedPathExists() {
                    return Filepath.exists(getSelectedPath())
                }

                property color fileExistsColor: _PaletteManager.isDarkPalette() ? Qt.darker(Colors.red, 2) : Qt.lighter(Colors.red, 1.5)
                
                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 10
                    
                    Rectangle {
                        Layout.fillWidth: true
                        height: filenameField.implicitHeight
                        color: selectionBar.selectedPathExists() ? selectionBar.fileExistsColor : root.activePalette.base
                        border.color: filenameField.activeFocus ? root.activePalette.accent : Qt.darker(root.activePalette.base, 1.4)
                        border.width: 1
                        radius: 5

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 0
                            spacing: 0

                            TextField {
                                id: filenameField
                                Layout.fillWidth: true
                                placeholderText: saveMode ? "Enter filename" : "Select a file"
                                selectByMouse: true
                                color: root.activePalette.text
                                font.pointSize: 9
                                background: Rectangle {
                                    color: "transparent"
                                }
                            }

                            DialogButton {
                                Layout.fillHeight: true
                                buttonIcon: MaterialIcons.add
                                ToolTip.text: "Increment version"
                                font.pointSize: 9
                                // font.bold: true
                                onClicked: {
                                    var filename = filenameField.text
                                    if (filename === "") return

                                    // Split filename and extension
                                    var lastDotIndex = filename.lastIndexOf(".")
                                    var baseName = ""
                                    var extension = ""
                                    
                                    if (lastDotIndex > 0) {
                                        baseName = filename.substring(0, lastDotIndex)
                                        extension = filename.substring(lastDotIndex)
                                    } else {
                                        baseName = filename
                                    }

                                    // Extract number at the end of basename
                                    var match = baseName.match(/^(.*?)(\d+)$/)
                                    if (match) {
                                        var prefix = match[1]
                                        var number = parseInt(match[2])
                                        filenameField.text = prefix + (number + 1) + extension
                                    } else {
                                        filenameField.text = baseName + "1" + extension
                                    }
                                }
                            }
                        }
                    }
                    
                    Button {
                        text: "Cancel"
                        background: Rectangle {
                            color: parent.hovered ? root.activePalette.accent : Qt.darker(root.activePalette.base, 1.4)
                            border.color: Qt.lighter(root.activePalette.base, 1.4)
                            border.width: 1
                            radius: 5
                        }
                        contentItem: Text {
                            text: parent.text
                            padding: 3
                            font.pointSize: 9
                            color: root.activePalette.text
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        onClicked: root.reject()
                    }
                    
                    Button {
                        text: saveMode ? "Save" : "Open"
                        highlighted: true
                        enabled: filenameField.text !== ""
                        background: Rectangle {
                            color: enabled ? (
                                parent.hovered ? root.activePalette.accent : Qt.darker(root.activePalette.base, 1.4)
                            ) : Qt.darker(root.activePalette.base, 2)
                            radius: 5
                        }
                        contentItem: Text {
                            text: parent.text
                            padding: 3
                            font.pointSize: 9
                            color: enabled ? root.activePalette.text : Qt.darker(root.activePalette.text, 2)
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            font.bold: true
                        }
                        onClicked: {
                            var path = selectionBar.getSelectedPath()
                            root.selectedFile = path
                            root.fileSelected(path)
                            root.accept()
                        }
                    }
                }
            }
        }
    }
}