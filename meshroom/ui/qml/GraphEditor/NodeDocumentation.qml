import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Controls 1.0

/**
 * Displays Node documentation
 */

FocusScope {
    id: root

    property variant node

    SystemPalette { id: activePalette }

    ScrollView {
        width: parent.width
        height: parent.height
        ScrollBar.vertical.policy: ScrollBar.AlwaysOn
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
        clip: true

        ColumnLayout {
            id: nodeDocColumnLayout
            property real keyColumnWidth: 10.0 * Qt.application.font.pixelSize

            Component {
                id: nodeInfoItem
                Rectangle {
                    color: activePalette.window
                    width: parent.width
                    height: childrenRect.height
                    RowLayout {
                        width: parent.width
                        Rectangle {
                            id: nodeInfoKey
                            anchors.margins: 2
                            color: Qt.darker(activePalette.window, 1.1)
                            Layout.preferredWidth: nodeDocColumnLayout.keyColumnWidth
                            Layout.minimumWidth: 0.2 * parent.width
                            Layout.maximumWidth: 0.8 * parent.width
                            Layout.fillWidth: false
                            Layout.fillHeight: true
                            Label {
                                text: modelData.key
                                anchors.fill: parent
                                anchors.top: parent.top
                                topPadding: 4
                                leftPadding: 6
                                verticalAlignment: TextEdit.AlignTop
                                elide: Text.ElideRight
                            }
                        }
                        // Drag handle for resizing
                        Rectangle {
                            width: 2
                            Layout.fillHeight: true
                            color: "transparent"
                            MouseArea {
                                anchors.fill: parent
                                anchors.margins: -2
                                cursorShape: Qt.SizeHorCursor
                                drag {
                                    target: parent
                                    axis: Drag.XAxis
                                    threshold: 0
                                    // Not required
                                    minimumX: 0.2 * nodeDocColumnLayout.width
                                    maximumX: 0.8 * nodeDocColumnLayout.width
                                }
                                onPositionChanged: (mouse)=> {
                                    nodeDocColumnLayout.keyColumnWidth = parent.x
                                }
                            }

                        }
                        TextArea {
                            id: nodeInfoValue
                            text: modelData.value
                            anchors.margins: 2
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            wrapMode: Label.WrapAtWordBoundaryOrAnywhere
                            textFormat: TextEdit.PlainText
                            readOnly: true
                            selectByMouse: true
                            background: Rectangle { anchors.fill: parent; color: Qt.darker(activePalette.window, 1.05) }
                        }
                    }
                }
            }

            ListView {
                id: nodeInfoListView
                width: parent.width
                height: childrenRect.height
                Layout.preferredWidth: width
                spacing: 3
                model: node.nodeInfos
                delegate: nodeInfoItem
            }

            TextEdit {
                id: documentationText
                anchors.top: nodeInfoListView.bottom
                padding: 8
                topPadding: 15
                Layout.preferredWidth: width
                width: parent.parent.parent.width
                textFormat: TextEdit.MarkdownText
                selectByMouse: true
                selectionColor: activePalette.highlight
                color: activePalette.text
                text: node ? node.documentation : ""
                wrapMode: TextEdit.Wrap
            }
        }
    }
}
