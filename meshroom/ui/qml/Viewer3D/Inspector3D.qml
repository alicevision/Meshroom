import QtQuick 2.7
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import MaterialIcons 2.2
import Qt3D.Core 2.0
import Qt3D.Render 2.1
import QtQuick.Controls.Material 2.4
import Controls 1.0
import Utils 1.0

FloatingPane {
    id: root

    implicitWidth: 200

    property int renderMode: 2
    property Transform targetTransform
    property Locator3D origin: null
    property Grid3D grid: null
    property MediaLibrary mediaLibrary
    property Camera camera

    signal mediaFocusRequest(var index)
    signal mediaRemoveRequest(var index)

    MouseArea { anchors.fill: parent; onWheel: wheel.accepted = true }

    ColumnLayout {
        width: parent.width
        height: parent.height
        spacing: 10

        Label { text: "RENDER"; font.bold: true; font.pointSize: 8 }
        Flow {
            Layout.fillWidth: true
            Repeater {
                model: Viewer3DSettings.renderModes

                delegate: MaterialToolButton {
                    text: modelData["icon"]
                    ToolTip.text: modelData["name"] + " (" + (index+1) + ")"
                    onClicked: Viewer3DSettings.renderMode = index
                    checked: Viewer3DSettings.renderMode === index
                }
            }
        }

        Label { text: "SCENE"; font.bold: true; font.pointSize: 8 }

        GridLayout {
            id: controlsLayout
            Layout.fillWidth: true
            columns: 3
            columnSpacing: 6
            Flow {
                Layout.columnSpan: 3
                Layout.fillWidth: true
                spacing: 0
                CheckBox {
                    text: "Grid"
                    checked: Viewer3DSettings.displayGrid
                    onClicked: Viewer3DSettings.displayGrid = !Viewer3DSettings.displayGrid
                }
                CheckBox {
                    text: "Locator"
                    checked: Viewer3DSettings.displayLocator
                    onClicked: Viewer3DSettings.displayLocator = !Viewer3DSettings.displayLocator
                }
            }

            // Rotation Controls
            Label {
                font.family: MaterialIcons.fontFamily
                text: MaterialIcons.rotation3D
                font.pointSize: 14
                Layout.rowSpan: 3
            }

            Slider { Layout.fillWidth: true; from: -180; to: 180; onPositionChanged: targetTransform.rotationX = value}
            Label { text: "X" }

            Slider { Layout.fillWidth: true;  from: -180; to: 180; onPositionChanged: targetTransform.rotationY = value}
            Label { text: "Y" }

            Slider { Layout.fillWidth: true;  from: -180; to: 180; onPositionChanged: targetTransform.rotationZ = value }
            Label { text: "Z" }

            Label { text: "Points" }
            RowLayout {
                Layout.columnSpan: 2
                Slider {
                    Layout.fillWidth: true; from: 1; to: 20;stepSize: 0.1
                    value: Viewer3DSettings.pointSize
                    onValueChanged: Viewer3DSettings.pointSize = value
                }
                CheckBox {
                    text: "Fixed";
                    checked: Viewer3DSettings.fixedPointSize
                    onClicked: Viewer3DSettings.fixedPointSize = !Viewer3DSettings.fixedPointSize
                }
            }

        }

        Label { text: "MEDIA"; font.bold: true; font.pointSize: 8 }

        ListView {
            id: mediaListView
            Layout.fillHeight: true
            Layout.fillWidth: true
            clip: true
            model: mediaLibrary.model
            spacing: 2
            //section.property: "section"

            ScrollBar.vertical: ScrollBar { id: scrollBar }

            section.delegate: Pane {
                width: parent.width
                padding: 1
                background: null

                Label {
                    width: parent.width
                    padding: 4
                    background: Rectangle { color: Qt.darker(parent.palette.base, 1.15) }
                    text: section
                }
            }

            Connections {
                target: mediaLibrary
                onLoadRequest: {
                    mediaListView.positionViewAtIndex(idx, ListView.Visible);
                }
            }

            delegate: RowLayout {
                // add mediaLibrary.count in the binding to ensure 'entity'
                // is re-evaluated when mediaLibrary delegates are modified
                property bool loading: model.status === SceneLoader.Loading
                spacing: 2
                width: parent.width - scrollBar.width / 2

                property string src: model.source
                onSrcChanged: focusAnim.restart()

                RowLayout {
                    Layout.alignment: Qt.AlignTop
                    spacing: 0

                    MaterialToolButton {
                        text: model.visible ? MaterialIcons.visibility : MaterialIcons.visibility_off
                        font.pointSize: 10
                        ToolTip.text: model.visible ? "Hide" : "Show"
                        flat: true
                        opacity: model.visible ? 1.0 : 0.6
                        onClicked: {
                            if(hoverArea.modifiers & Qt.ControlModifier)
                                mediaLibrary.solo(index);
                            else
                                model.visible = !model.visible
                        }
                        // Handle modifiers on button click
                        MouseArea {
                            id: hoverArea
                            property int modifiers
                            anchors.fill: parent
                            hoverEnabled: true
                            onPositionChanged: modifiers = mouse.modifiers
                            onExited: modifiers = Qt.NoModifier
                            onPressed: {
                                modifiers = mouse.modifiers;
                                mouse.accepted = false;
                            }
                        }
                    }
                    MaterialToolButton {
                        text: MaterialIcons.filter_center_focus
                        font.pointSize: 10
                        ToolTip.text: "Frame"
                        onClicked: camera.viewEntity(mediaLibrary.entityAt(index))
                        flat: true
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 1
                    Layout.alignment: Qt.AlignTop

                    Label {
                        id: label
                        leftPadding: 0
                        rightPadding: 0
                        topPadding: 3
                        bottomPadding: topPadding
                        Layout.fillWidth: true
                        text: model.label
                        elide: Text.ElideMiddle
                        background: Rectangle {
                            Connections {
                                target: mediaLibrary
                                onLoadRequest: if(idx == index) focusAnim.restart()
                            }
                            ColorAnimation on color {
                                id: focusAnim
                                from: label.palette.highlight
                                to: "transparent"
                                duration: 2000
                            }
                            MouseArea {
                                anchors.fill: parent
                                onDoubleClicked: camera.viewEntity(mediaLibrary.entityAt(index))
                            }
                        }
                    }
                    Item {
                        Layout.fillWidth: true
                        implicitHeight: childrenRect.height
                        RowLayout {
                            visible: model.status === SceneLoader.Ready
                            MaterialLabel { visible: model.vertexCount; text: MaterialIcons.grain }
                            Label { visible: model.vertexCount; text: Format.intToString(model.vertexCount) }
                            MaterialLabel { visible: model.faceCount; text: MaterialIcons.details; rotation: -180 }
                            Label { visible: model.faceCount; text: Format.intToString(model.faceCount) }
                            MaterialLabel { visible: model.cameraCount; text: MaterialIcons.videocam }
                            Label { visible: model.cameraCount; text: model.cameraCount }
                            MaterialLabel { visible: model.textureCount; text: MaterialIcons.texture }
                            Label { visible: model.textureCount; text: model.textureCount }
                        }
                    }
                }

                // Media unavailability indicator
                MaterialToolButton {
                    Layout.alignment: Qt.AlignTop
                    enabled: false
                    visible: !model.valid
                    text: MaterialIcons.no_sim
                    font.pointSize: 10
                }

                // Remove media from library button
                MaterialToolButton {
                    id: removeButton
                    Layout.alignment: Qt.AlignTop

                    visible: !loading
                    text: MaterialIcons.clear
                    font.pointSize: 10
                    ToolTip.text: "Remove"
                    onClicked: mediaLibrary.remove(index)
                }

                // Media loading indicator
                BusyIndicator {
                    visible: loading
                    running: visible
                    padding: removeButton.padding
                    implicitHeight: implicitWidth
                    implicitWidth: removeButton.width
                }
            }
        }
    }
}
