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
    property Grid3D grid: null
    property MediaLibrary mediaLibrary
    property Camera camera
    property var uigraph: null

    signal mediaFocusRequest(var index)
    signal mediaRemoveRequest(var index)

    padding: 0

    MouseArea { anchors.fill: parent; onWheel: wheel.accepted = true }

    ColumnLayout {
        anchors.fill: parent
        spacing: 4

        Group {
            Layout.fillWidth: true
            title: "SETTINGS"

            GridLayout {
                width: parent.width
                columns: 2
                columnSpacing: 6
                rowSpacing: 3

                MaterialLabel { font.family: MaterialIcons.fontFamily; text: MaterialIcons.grain; padding: 2 }
                RowLayout {
                    Slider {
                        Layout.fillWidth: true; from: 0; to: 5; stepSize: 0.1
                        value: Viewer3DSettings.pointSize
                        onValueChanged: Viewer3DSettings.pointSize = value
                        ToolTip.text: "Point Size: " + value.toFixed(2)
                        ToolTip.visible: hovered || pressed
                        ToolTip.delay: 150
                    }
                    MaterialToolButton {
                        text: MaterialIcons.center_focus_strong
                        ToolTip.text: "Fixed Point Size"
                        font.pointSize: 10
                        padding: 3
                        checked: Viewer3DSettings.fixedPointSize
                        onClicked: Viewer3DSettings.fixedPointSize = !Viewer3DSettings.fixedPointSize
                    }

                }
                MaterialLabel { font.family: MaterialIcons.fontFamily; text: MaterialIcons.videocam; padding: 2 }
                Slider {
                    value: Viewer3DSettings.cameraScale
                    from: 0
                    to: 2
                    stepSize: 0.01
                    Layout.fillWidth: true
                    padding: 0
                    onMoved: Viewer3DSettings.cameraScale = value
                    ToolTip.text: "Camera Scale: " + value.toFixed(2)
                    ToolTip.visible: hovered || pressed
                    ToolTip.delay: 150
                }
                Flow {
                    Layout.columnSpan: 2
                    Layout.fillWidth: true
                    spacing: 2
                    CheckBox {
                        text: "Grid"
                        padding: 2
                        checked: Viewer3DSettings.displayGrid
                        onClicked: Viewer3DSettings.displayGrid = !Viewer3DSettings.displayGrid
                    }
                    CheckBox {
                        text: "Gizmo"
                        padding: 2
                        checked: Viewer3DSettings.displayGizmo
                        onClicked: Viewer3DSettings.displayGizmo = !Viewer3DSettings.displayGizmo
                    }
                    CheckBox {
                        text: "Origin"
                        padding: 2
                        checked: Viewer3DSettings.displayOrigin
                        onClicked: Viewer3DSettings.displayOrigin = !Viewer3DSettings.displayOrigin
                    }
                }
            }
        }

        // 3D Scene content
        Group {
            title: "SCENE"
            Layout.fillWidth: true
            Layout.fillHeight: true
            sidePadding: 0

            toolBarContent: MaterialToolButton {
                id: infoButton
                ToolTip.text: "Media Info"
                text: MaterialIcons.info_outline
                font.pointSize: 10
                implicitHeight: parent.height
                checkable: true
                checked: true
                padding: 0
            }

            ListView {
                id: mediaListView
                anchors.fill: parent
                clip: true
                model: mediaLibrary.model
                spacing: 4

                ScrollBar.vertical: ScrollBar { id: scrollBar }

                currentIndex: -1

                Connections {
                    target: uigraph
                    onSelectedNodeChanged: mediaListView.currentIndex = -1
                }

                Connections {
                    target: mediaLibrary
                    onLoadRequest: {
                        mediaListView.positionViewAtIndex(idx, ListView.Visible);
                    }
                }

                delegate: RowLayout {
                    id: mediaDelegate
                    // add mediaLibrary.count in the binding to ensure 'entity'
                    // is re-evaluated when mediaLibrary delegates are modified
                    property bool loading: model.status === SceneLoader.Loading
                    spacing: 2
                    width: parent.width - scrollBar.width / 2

                    property string src: model.source
                    onSrcChanged: focusAnim.restart()

                    property bool hovered:  model.attribute ? uigraph.hoveredNode === model.attribute.node : mouseArea.containsMouse
                    property bool isSelectedNode: model.attribute ? uigraph.selectedNode === model.attribute.node : false

                    function updateCurrentIndex() {
                        if(isSelectedNode) { mediaListView.currentIndex = index }
                    }

                    onIsSelectedNodeChanged: updateCurrentIndex()

                    Connections {
                        target: mediaListView
                        onCountChanged: mediaDelegate.updateCurrentIndex()
                    }

                    // Current/selected element indicator
                    Rectangle {
                        Layout.fillHeight: true
                        width: 2
                        color: {
                            if(mediaListView.currentIndex == index || mediaDelegate.isSelectedNode)
                                return label.palette.highlight;
                            if(mediaDelegate.hovered)
                                return Qt.darker(label.palette.highlight, 1.5);
                            return "transparent";
                        }
                    }

                    // Media visibility/loading control
                    MaterialToolButton {
                        Layout.alignment: Qt.AlignTop
                        text: model.visible ? MaterialIcons.visibility : MaterialIcons.visibility_off
                        font.pointSize: 10
                        ToolTip.text: model.visible ? "Hide" : model.requested ? "Show" : model.valid ? "Load and Show" : "Load and Show when Available"
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

                    // Media label and info
                    Item {
                        implicitHeight: childrenRect.height
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignTop
                        ColumnLayout {
                            id: centralLayout
                            width: parent.width
                            spacing: 1

                            Label {
                                id: label
                                Layout.fillWidth: true
                                leftPadding: 0
                                rightPadding: 0
                                topPadding: 3
                                bottomPadding: topPadding
                                text: model.label
                                opacity: model.valid ? 1.0 : 0.6
                                elide: Text.ElideMiddle
                                font.weight: mediaListView.currentIndex == index ? Font.DemiBold : Font.Normal
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
                                }
                            }
                            Item {
                                visible: infoButton.checked
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
                        MouseArea {
                            id: mouseArea
                            anchors.fill: centralLayout
                            hoverEnabled: true
                            acceptedButtons: Qt.AllButtons
                            onEntered: { if(model.attribute) uigraph.hoveredNode = model.attribute.node }
                            onExited: { if(model.attribute) uigraph.hoveredNode = null }
                            onClicked: {
                                if(model.attribute)
                                    uigraph.selectedNode = model.attribute.node;
                                else
                                    uigraph.selectedNode = null;
                                if(mouse.button == Qt.RightButton)
                                    contextMenu.popup();
                                mediaListView.currentIndex = index;
                            }
                            onDoubleClicked: {
                                model.visible = true;
                                camera.viewEntity(mediaLibrary.entityAt(index));
                            }
                        }

                        Menu {
                            id: contextMenu
                            MenuItem {
                                text: "Open Containing Folder"
                                enabled: model.valid
                                onTriggered: Qt.openUrlExternally(Filepath.dirname(model.source))
                            }
                            MenuItem {
                                text: "Copy Path"
                                // hidden TextEdit to copy to clipboard
                                TextEdit { id: fullpath; visible: false; text: Filepath.normpath(model.source) }
                                onTriggered: { fullpath.selectAll(); fullpath.copy(); }
                            }
                            MenuSeparator {}
                            MenuItem {
                                text: model.requested ? "Unload Media" : "Load Media"
                                enabled: model.valid
                                onTriggered: model.requested = !model.requested
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
}
