import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import MaterialIcons 2.2
import Qt.labs.platform 1.0 as Platform

import Controls 1.0

/**
 * LiveSfMView provides controls for setting up and starting a live reconstruction.
 */

Panel {
    id: root

    property variant reconstruction
    readonly property variant liveSfmManager: reconstruction ? reconstruction.liveSfmManager : null

    title: "Live Reconstruction"
    icon: Label {
        text: MaterialIcons.linked_camera;
        font.family: MaterialIcons.fontFamily;
        font.pixelSize: 13
    }

    padding: 2
    clip: true

    Platform.FolderDialog {
        id: selectFolderDialog
        title: "Live Reconstruction - Select Image Folder"
        onAccepted: {
            folderPath.text = Filepath.urlToString(folder)
        }
    }

    // Options
    Pane {
        width: parent.width
        Layout.alignment: Qt.AlignTop
        ColumnLayout {
            width: parent.width
            GroupBox {
                Layout.fillWidth: true
                enabled: liveSfmManager ? !liveSfmManager.running : false

                GridLayout {
                    width: parent.width
                    columnSpacing: 12
                    columns: 2

                    Label {
                        text: "Image Folder"
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 0
                        TextField {
                            id: folderPath
                            Layout.fillWidth: true
                            selectByMouse: true
                            text: liveSfmManager ? liveSfmManager.folder : ""
                            placeholderText: "Select a Folder"
                        }
                        ToolButton {
                            text: MaterialIcons.folder
                            font.family: MaterialIcons.fontFamily
                            onClicked: selectFolderDialog.open()
                            ToolTip.text: "Select Folder in which Images will be progressively added for Live Reconstruction"
                            ToolTip.visible: hovered
                            ToolTip.delay: 200
                        }
                    }

                    Label {
                        text: "Min. Images per Step"
                    }

                    SpinBox {
                        id: minImg_SB
                        editable: true
                        from: 2
                        value: 4
                        to: 50
                        implicitWidth: 50
                    }
                }
            }

            Button {                
                Layout.alignment: Qt.AlignCenter
                text: checked ? "Stop" : "Start"
                enabled: liveSfmManager ? liveSfmManager.running || folderPath.text.trim() != '' : false
                checked: liveSfmManager ? liveSfmManager.running : false
                onClicked: {
                    if (!liveSfmManager.running)
                        liveSfmManager.start(folderPath.text, minImg_SB.value)
                    else
                        liveSfmManager.stop()
                }
            }
        }
    }
}
