import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform as Platform

import MaterialIcons 2.2
import Utils 1.0

/**
 * "Save As Template" dialog: the template file and its metadata (header "templateInfo") shown on the homepage.
 *
 * Category colors come from MeshroomApp (built-in table, otherwise hashed from the lower-case name).
 * Icons are MaterialIcons names; without icon, nothing is written.
 */
Dialog {
    id: root

    // Emitted with the template file and the edited metadata when the user saves
    signal saveRequested(url fileUrl, var info)

    readonly property string extension: ".mgt"
    readonly property string legacyExtension: ".mg"
    // Default folder when no template file is given (url, so that it can be set by initFileDialogFolder)
    property url folder
    property string category: ""
    property string icon: ""
    // Categories of the registered templates, read when the dialog opens
    property var knownCategories: []
    // Categories added in this dialog, not used by any registered template yet
    property var extraCategories: []

    // Result of the check of the typed path (updateStatus)
    property string filePath: ""
    property string templateKey: ""
    property string statusText: ""
    // "error": the template cannot be saved, "warning": the file will be replaced, "": the file will be created
    property string statusLevel: "error"
    readonly property bool canSave: statusLevel !== "error"
    readonly property color statusColor: statusLevel === "error" ? Colors.red : statusLevel === "warning" ? Colors.orange : palette.text
    readonly property color categoryColor: MeshroomApp.templateCategoryColor(category)
    readonly property var categories: [""].concat(knownCategories, extraCategories)

    /**
     * Check the typed template path: update the file to write, the template key and the footer status.
     * The extension is added when there is none; the file name without extension is the template key.
     */
    function updateStatus() {
        const typedPath = pathField.text.trim()
        const name = typedPath ? Filepath.basename(typedPath) : ""
        const dot = name.lastIndexOf(".")
        const typedExtension = dot >= 0 ? name.slice(dot) : ""
        const key = dot >= 0 ? name.slice(0, dot) : name
        const path = !typedPath ? "" : typedExtension ? typedPath : typedPath + extension
        const parentFolder = path ? Filepath.dirname(path) : ""

        let error = ""
        if (!typedPath)
            error = "Enter the path of the template file, or Browse..."
        else if (!parentFolder)
            error = "Enter the full path of the template file."
        else if (!Filepath.exists(parentFolder))
            error = "Folder not found: " + parentFolder
        else if (!key)
            error = "Enter a file name."
        else if (typedExtension && typedExtension.toLowerCase() !== extension)
            error = "Templates must use the " + extension + " extension, not " + typedExtension + "."

        templateKey = key
        filePath = error ? "" : path
        if (error) {
            statusLevel = "error"
            statusText = error
        } else if (Filepath.exists(path)) {
            statusLevel = "warning"
            statusText = Filepath.basename(path) + " exists and will be replaced."
        } else {
            statusLevel = ""
            statusText = "Creates " + Filepath.basename(path)
        }
    }

    /**
     * Open the dialog pre-filled with the template metadata `info`.
     * If `path` is set, it is the template file; otherwise the path starts with the default `folder`.
     */
    function openWith(path, info) {
        const defaultFolder = folder.toString() ? Filepath.urlToString(folder) : ""
        // A legacy template is saved with the template extension
        if (path && path.toLowerCase().endsWith(legacyExtension))
            path = path.slice(0, path.length - legacyExtension.length) + extension
        pathField.text = path || (defaultFolder ? defaultFolder + "/" : "")
        // The file may have been created or removed since the last time: check it even if the text did not change
        updateStatus()
        labelField.text = info.label || ""
        category = info.category || ""
        icon = info.icon || ""
        descriptionField.text = info.description || ""
        knownCategories = MeshroomApp.templateCategories()
        extraCategories = []
        // A category of the template that is not offered yet is shown with the others
        if (category && !containsCategory(categories, category))
            extraCategories = [category]
        newCategoryRow.visible = false
        iconSearch.clear()
        open()
        pathField.cursorPosition = pathField.text.length
        pathField.forceActiveFocus()
    }

    Connections {
        target: pathField
        function onTextChanged() { root.updateStatus() }
    }

    function containsCategory(list, name) {
        return list.some(c => c.toLowerCase() === name.trim().toLowerCase())
    }

    function addCategory(name) {
        name = name.trim()
        if (!name)
            return
        // Names match case-insensitively: reuse the existing spelling
        const existing = categories.find(c => c && c.toLowerCase() === name.toLowerCase())
        if (existing) {
            category = existing
        } else {
            extraCategories = extraCategories.concat([name])
            category = name
        }
        newCategoryRow.visible = false
    }

    function save() {
        if (!canSave)
            return
        saveRequested(Filepath.stringToUrl(filePath), {
            "label": labelField.text,
            "category": category,
            "icon": icon,
            "description": descriptionField.text
        })
        close()
    }

    // Text field with the look of the attribute editor fields (AttributeControls/TextFieldRow)
    component FormTextField: TextField {
        property bool error: false
        selectByMouse: true
        placeholderTextColor: "gray"
        background: Rectangle {
            color: Qt.darker(palette.window, 1.2)
            border.color: parent.error ? "orange" : parent.activeFocus ? palette.highlight : "transparent"
            radius: 2
        }
    }

    // Small bold title above each field
    component FieldTitle: Label {
        font.bold: true
    }

    title: "Save As Template"
    modal: true
    // Escape first closes the new category input
    closePolicy: newCategoryRow.visible ? Popup.NoAutoClose : Popup.CloseOnEscape
    width: 640
    x: parent ? (parent.width - width) / 2 : 0
    y: parent ? Math.max(0, (parent.height - height) / 2) : 0
    height: parent ? Math.min(implicitHeight, parent.height - 20) : implicitHeight
    padding: 16

    Platform.FileDialog {
        id: browseDialog
        title: "Save Template"
        nameFilters: ["Meshroom Templates (*.mgt)"]
        defaultSuffix: root.extension
        fileMode: Platform.FileDialog.SaveFile
        onAccepted: {
            pathField.text = Filepath.urlToString(currentFile)
        }
    }

    contentItem: ScrollView {
        id: scrollView
        clip: true
        contentWidth: availableWidth
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

        ColumnLayout {
            width: scrollView.availableWidth
            spacing: 14

            // File: the template path; its file name is the template key
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4
                FieldTitle { text: "File" }
                RowLayout {
                    Layout.fillWidth: true
                    FormTextField {
                        id: pathField
                        Layout.fillWidth: true
                        placeholderText: "/path/to/templateName" + root.extension
                        error: text.trim() !== "" && !root.canSave
                        ToolTip.text: "The file name is also the template key: projects created from it store it as their source template."
                        ToolTip.visible: hovered
                        ToolTip.delay: 500
                        onAccepted: root.save()
                    }
                    MaterialToolLabelButton {
                        id: browseButton
                        Layout.preferredHeight: pathField.height
                        leftPadding: 8
                        rightPadding: 10
                        iconText: MaterialIcons.folder_open
                        label: "Browse..."
                        background: Rectangle {
                            radius: 2
                            color: browseButton.pressed ? Qt.darker(palette.button, 1.2)
                                 : browseButton.hovered ? Qt.lighter(palette.button, 1.15) : palette.button
                            border.color: palette.mid
                        }
                        ToolTip.text: "Choose the folder and file name of the template"
                        onClicked: {
                            const parentFolder = root.filePath ? Filepath.dirname(root.filePath) : ""
                            if (parentFolder)
                                browseDialog.folder = Filepath.stringToUrl(parentFolder)
                            browseDialog.open()
                        }
                    }
                }
            }

            // Category: one chip per category, with the category color
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 6
                FieldTitle { text: "Category" }
                Flow {
                    Layout.fillWidth: true
                    spacing: 6
                    Repeater {
                        model: root.categories
                        delegate: MaterialToolLabelButton {
                            id: chip
                            required property string modelData
                            readonly property bool selected: root.category.toLowerCase() === modelData.toLowerCase()
                            height: 28
                            leftPadding: 10
                            rightPadding: 12
                            iconText: MaterialIcons.square
                            iconSize: 10
                            iconItem.color: MeshroomApp.templateCategoryColor(modelData)
                            label: modelData || "None"
                            labelItem.color: palette.text
                            onClicked: root.category = modelData
                            background: Rectangle {
                                radius: height / 2
                                color: chip.selected ? Qt.rgba(palette.highlight.r, palette.highlight.g, palette.highlight.b, 0.25)
                                     : chip.hovered ? Qt.lighter(palette.window, 1.15) : Qt.darker(palette.window, 1.1)
                                border.color: chip.selected ? palette.highlight : palette.mid
                            }
                        }
                    }
                    MaterialToolLabelButton {
                        id: newCategoryButton
                        visible: !newCategoryRow.visible
                        height: 28
                        leftPadding: 10
                        rightPadding: 12
                        iconText: MaterialIcons.add
                        iconSize: 11
                        label: "New Category"
                        onClicked: {
                            newCategoryField.text = ""
                            newCategoryRow.visible = true
                            newCategoryField.forceActiveFocus()
                        }
                        background: Rectangle {
                            radius: height / 2
                            color: newCategoryButton.hovered ? Qt.lighter(palette.window, 1.15) : "transparent"
                            border.color: palette.mid
                        }
                    }
                }
                RowLayout {
                    id: newCategoryRow
                    Layout.fillWidth: true
                    visible: false
                    MaterialLabel {
                        text: MaterialIcons.square
                        font.pointSize: 13
                        color: MeshroomApp.templateCategoryColor(newCategoryField.text)
                    }
                    FormTextField {
                        id: newCategoryField
                        Layout.fillWidth: true
                        placeholderText: "Category name"
                        onAccepted: root.addCategory(text)
                        Keys.onEscapePressed: (event) => {
                            // Close the new category input, not the dialog
                            event.accepted = true
                            newCategoryRow.visible = false
                        }
                    }
                    MaterialToolButton {
                        text: MaterialIcons.check
                        enabled: newCategoryField.text.trim() !== ""
                        ToolTip.text: "Add the category"
                        onClicked: root.addCategory(newCategoryField.text)
                    }
                    MaterialToolButton {
                        text: MaterialIcons.close
                        ToolTip.text: "Cancel"
                        onClicked: newCategoryRow.visible = false
                    }
                }
            }

            // Label
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4
                FieldTitle { text: "Label" }
                FormTextField {
                    id: labelField
                    Layout.fillWidth: true
                    // Empty: derived from the file name
                    placeholderText: MeshroomApp.defaultTemplateLabel(root.templateKey) || "Label"
                }
            }

            // Description, with the look of the attribute editor text areas (AttributeControls/TextAreaFlick)
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4
                FieldTitle { text: "Description" }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 60
                    color: palette.base
                    radius: 2
                    border.color: descriptionField.activeFocus ? palette.highlight : "transparent"
                    Flickable {
                        anchors.fill: parent
                        anchors.margins: 1
                        contentWidth: width
                        clip: true
                        ScrollBar.vertical: MScrollBar {}
                        TextArea.flickable: TextArea {
                            id: descriptionField
                            wrapMode: TextEdit.Wrap
                            selectByMouse: true
                            placeholderText: "One sentence: what goes in, what comes out."
                            placeholderTextColor: "gray"
                            background: Item {}
                        }
                    }
                }
            }

            // Icon: preview + search through MaterialIcons; no icon means the default one and nothing is written
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 6
                FieldTitle { text: "Icon" }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    // Selected icon, as high as the search bar; a click removes the icon
                    MaterialToolButton {
                        Layout.preferredHeight: iconSearch.height
                        Layout.preferredWidth: iconSearch.height
                        padding: 0
                        font.pointSize: 14
                        textColor: root.categoryColor
                        // No icon (or an unknown name): an empty box
                        text: MaterialIcons[root.icon] || ""
                        ToolTip.text: root.icon ? root.icon + " (click to remove the icon)" : "No icon"
                        onClicked: root.icon = ""
                        background: Rectangle {
                            radius: 2
                            color: Qt.darker(palette.window, 1.2)
                        }
                    }
                    SearchBar {
                        id: iconSearch
                        Layout.fillWidth: true
                        textField.placeholderText: "Search icons"
                        textField.placeholderTextColor: "gray"
                        // Enter picks the first match
                        onAccepted: {
                            if (iconGrid.count > 0)
                                root.icon = iconGrid.model[0]
                        }
                    }
                }
                GridView {
                    id: iconGrid
                    Layout.fillWidth: true
                    Layout.preferredHeight: 2 * cellHeight
                    clip: true
                    cellWidth: width / Math.max(1, Math.floor(width / 80))
                    cellHeight: 60
                    ScrollBar.vertical: MScrollBar {}
                    // Default icons while nothing is searched
                    model: MeshroomApp.searchTemplateIcons(iconSearch.text)
                    delegate: ToolButton {
                        id: iconTile
                        required property string modelData
                        readonly property bool selected: root.icon === modelData
                        width: iconGrid.cellWidth - 6
                        height: iconGrid.cellHeight - 6
                        onClicked: root.icon = modelData
                        ToolTip.text: modelData
                        ToolTip.visible: hovered
                        ToolTip.delay: 500
                        contentItem: ColumnLayout {
                            spacing: 2
                            MaterialLabel {
                                Layout.alignment: Qt.AlignHCenter
                                font.pointSize: 15
                                color: iconTile.selected ? root.categoryColor : palette.text
                                text: MaterialIcons[iconTile.modelData] || ""
                            }
                            Label {
                                Layout.fillWidth: true
                                horizontalAlignment: Text.AlignHCenter
                                elide: Text.ElideRight
                                font.pointSize: 7
                                opacity: iconTile.selected ? 1.0 : 0.7
                                text: iconTile.modelData
                            }
                        }
                        background: Rectangle {
                            radius: 4
                            color: iconTile.selected ? Qt.rgba(palette.highlight.r, palette.highlight.g, palette.highlight.b, 0.25)
                                 : iconTile.hovered ? Qt.lighter(palette.window, 1.15) : Qt.darker(palette.window, 1.1)
                            border.color: iconTile.selected ? palette.highlight : "transparent"
                        }
                    }
                    Label {
                        anchors.centerIn: parent
                        visible: iconGrid.count === 0
                        opacity: 0.6
                        text: "No icon matches \"" + iconSearch.text.trim() + "\"."
                    }
                }
            }
        }
    }

    footer: Pane {
        background: Item {}
        padding: 12
        RowLayout {
            anchors.fill: parent
            spacing: 8
            Label {
                Layout.fillWidth: true
                elide: Text.ElideRight
                color: root.statusColor
                opacity: root.statusLevel === "" ? 0.7 : 1.0
                text: root.statusText
                ToolTip.text: text
                ToolTip.visible: truncated && statusMouseArea.containsMouse
                MouseArea { id: statusMouseArea; anchors.fill: parent; hoverEnabled: true }
            }
            Button {
                text: "Cancel"
                onClicked: root.reject()
            }
            Button {
                text: root.statusLevel === "warning" ? "Replace Template" : "Save Template"
                enabled: root.canSave
                highlighted: true
                onClicked: root.save()
            }
        }
    }
}
