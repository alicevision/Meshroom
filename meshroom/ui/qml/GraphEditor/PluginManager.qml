import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform 1.0 as Platform
import MaterialIcons 2.2
import Controls 1.0
import Utils 1.0

/**
 * PluginManager displays available plugins within Meshroom context and allows loading new ones.
*/
Dialog {
    id: root

    // the UIGraph instance
    property var uigraph
    // the Plugin Manager instance
    property var manager
    // alias to underlying plugin model
    readonly property var pluginsModel: manager ? manager.plugins : undefined

    // Does not allow any other element outside the dialog to be interacted with till the time this window is open
    modal: true

    // Positioning of the Dialog in the screen
    x: parent.width / 2 - width / 2
    y: parent.height / 2 - height / 2

    // Bounds
    height: 600

    // Signals
    signal browsed(var directory)

    title: "Node Plugin Manager"

    ColumnLayout {
        anchors.fill: parent
        spacing: 16

        ListView {
            id: listView

            // Bounds
            Layout.preferredWidth: 600
            Layout.fillHeight: true
            implicitHeight: contentHeight

            clip: true
            model: pluginsModel

            ScrollBar.vertical: MScrollBar { id: scrollbar }

            spacing: 4
            headerPositioning: ListView.OverlayHeader
            header: Pane {
                z: 2
                width: ListView.view.width
                padding: 6
                background: Rectangle { color: Qt.darker(parent.palette.window, 1.15) }
                RowLayout {
                    id: headerLabel
                    width: parent.width
                    Label { text: "Plugin"; Layout.preferredWidth: 160; font.bold: true }
                    Label { text: "Status"; Layout.preferredWidth: 70; font.bold: true }
                    Label { text: "Version"; Layout.preferredWidth: 70; font.bold: true }
                }
            }

            delegate: RowLayout {
                id: pluginDelegate

                property var plugin: object

                width: ListView.view.width - 12
                anchors.horizontalCenter: parent != null ? parent.horizontalCenter : undefined

                Label {
                    Layout.preferredWidth: 200
                    text: pluginDelegate.plugin ? pluginDelegate.plugin.name : ""

                    // Mouse Area to allow clicking on the label
                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            metadataPane.plugin = pluginDelegate.plugin
                            metadataPane.visible = true
                        }
                    }
                }
                Label {
                    id: status
                    Layout.preferredWidth: 90
                    text: pluginDelegate.plugin && pluginDelegate.plugin.loaded ? MaterialIcons.check : MaterialIcons.clear
                    color: pluginDelegate.plugin && pluginDelegate.plugin.loaded ? "#4CAF50" : "#F44336"
                    font.family: MaterialIcons.fontFamily
                    font.pointSize: 14
                    font.bold: true
                }
                Label {
                    id: version
                    Layout.preferredWidth: 50
                    text: pluginDelegate.plugin ? pluginDelegate.plugin.version : ""
                }

                // Reload the Plugin
                MaterialToolButton {
                    id: reloader

                    text: MaterialIcons.refresh
                    ToolTip.text: "Reload Plugin"

                    onClicked: {
                        if (pluginDelegate.plugin) {
                            // Dialog items for updates
                            confirmationDialog.statusItem = status
                            confirmationDialog.versionItem = version

                            // Plugin for 
                            confirmationDialog.plugin = pluginDelegate.plugin

                            // Show the confirmation dialog to the user
                            confirmationDialog.open()
                        }
                    }
                }
            }
        }

        // Bottom pane for showing plugin related information
        Pane {
            id: metadataPane

            // the plugin to display info for
            property var plugin

            // Hidden as default
            visible: false

            // Bounds
            anchors.topMargin: 0
            Layout.fillWidth: true
            Layout.preferredHeight: 200

            // Clip additional content
            clip: true

            background: Rectangle { color: Qt.darker(parent.palette.window, 1.15) }

            // Header
            Label { id: infoLabel; text: ( metadataPane.plugin ? metadataPane.plugin.name : "Plugin" ) + " Info"; font.bold: true; }

            MaterialToolButton {
                id: paneCloser
                text: MaterialIcons.close

                // Alignment
                anchors.right: parent.right
                anchors.verticalCenter: infoLabel.verticalCenter

                onClicked: { metadataPane.visible = false }
            }

            ScrollView {
                // Bounds
                anchors.top: paneCloser.bottom
                width: parent.width
                height: parent.height - paneCloser.height

                // clip anything going beyond the boundary
                clip: true

                background: Rectangle { color: Qt.darker(parent.palette.window, 1.65) }

                Column {
                    width: parent.width

                    RowLayout {
                        Label { text: "Name:"; Layout.preferredWidth: 100; font.bold: true }
                        TextArea { text: metadataPane.plugin ? metadataPane.plugin.name : ""; readOnly: true }
                    }

                    // File Path
                    RowLayout {
                        Label { text: "File Path:"; Layout.preferredWidth: 100; font.bold: true }
                        TextArea {
                            text: metadataPane.plugin ? metadataPane.plugin.path : ""
                            Layout.preferredWidth: 450
                            wrapMode: Text.WordWrap
                            readOnly: true
                            selectByMouse: true
                        }
                    }

                    // Load Status
                    RowLayout {
                        Label { text: "Status:"; Layout.preferredWidth: 100; font.bold: true }
                        TextArea { text: metadataPane.plugin && metadataPane.plugin.loaded ? "Loaded" : "Errored"; readOnly: true }
                    }

                    // Empty
                    RowLayout { }

                    // Load Status
                    RowLayout {
                        Label { text: "Documentation:"; Layout.preferredWidth: 100; font.bold: true }
                        TextArea {
                            text: metadataPane.plugin ? metadataPane.plugin.documentation : ""
                            Layout.preferredWidth: 450
                            wrapMode: Text.WordWrap
                            readOnly: true
                        }
                    }

                    // Empty
                    RowLayout { }

                    RowLayout {
                        Label { text: "Errors:"; Layout.preferredWidth: 100; font.bold: true }
                        TextArea {
                            text: metadataPane.plugin ? metadataPane.plugin.errors : ""
                            Layout.preferredWidth: 450
                            wrapMode: Text.WordWrap
                            readOnly: true
                            selectByMouse: true
                        }
                    }
                }
            }
        }
    }

    /// Buttons footer
    footer: DialogButtonBox {
        position: DialogButtonBox.Footer

        // Plugin Browser
        Button {
            text: "Browse"

            onClicked: {
                // Show the dialog to allow browsing of plugins package
                loadDialog.open()
            }
        }

        // Close the plugin manager
        Button {
            text: "Close"

            onClicked: {
                root.close()
            }
        }
    }

    /// The widget should only get closed when either Esc is pressed or Close button is clicked
    closePolicy: Popup.CloseOnEscape

    // Folder selecting dialog
    Platform.FolderDialog {
        id: loadDialog
        options: Platform.FileDialog.DontUseNativeDialog

        title: "Browse Plugin Package"
        acceptLabel: "Select"

        onAccepted: {
            // Emit that a directory has been browsed -> for the loading to occur
            root.browsed(loadDialog.folder)
        }
    }

    // A Confirmation Dialog to prompt user of the awareness of the reload process
    MessageDialog  {
        id: confirmationDialog

        focus: true
        modal: true
        header.visible: false

        text: "Reloading a Plugin will affect all the Node instances of the plugin in the graph.\nDo you want to proceed with reloading?"
        helperText: "Warning: This operation cannot be undone."
        standardButtons: Dialog.Yes | Dialog.Cancel

        property var plugin: null   // plugin to reload
        property var statusItem: null   // status item to update the text for once the plugin has been reloaded
        property var versionItem: null  // version item to update the text for once the plugin has been reloaded

        onAccepted: {
            // All of the items required before calling for a reload
            if (!plugin || !statusItem || !versionItem) return

            // Reload
            let ret = plugin.reload()

            // Return if the plugin was not reloaded
            if (!ret) return

            // Reload the Node instances in the graph
            root.uigraph.reloadNodes(plugin.name)

            // Update the status and version, in case they have changed
            statusItem.text = plugin.loaded ? MaterialIcons.check : MaterialIcons.clear
            statusItem.color = plugin.loaded ? "#4CAF50" : "#F44336"

            versionItem.text = plugin.version

            // Update the plugin details view
            metadataPane.plugin = plugin
        }
    }
}
