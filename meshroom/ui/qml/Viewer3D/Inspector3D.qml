import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt3D.Core 2.6
import Qt3D.Render 2.6

import Controls 1.0
import MaterialIcons 2.2
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
    signal nodeActivated(var node)

    padding: 0

    MouseArea {
        anchors.fill: parent
        onWheel: function(wheel) {
            wheel.accepted = true
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 4

        ExpandableGroup {
            id: displayGroup
            Layout.fillWidth: true
            title: "DISPLAY"

            GridLayout {
                width: parent.width
                columns: 2
                columnSpacing: 6
                rowSpacing: 3
                Flow {
                    Layout.columnSpan: 2
                    Layout.fillWidth: true
                    visible: displayGroup.expanded
                    spacing: 1
                    MaterialToolButton {
                        text: MaterialIcons.grid_on
                        ToolTip.text: "Display Grid"
                        checked: Viewer3DSettings.displayGrid
                        onClicked: Viewer3DSettings.displayGrid = !Viewer3DSettings.displayGrid
                    }
                    MaterialToolButton {
                        text: MaterialIcons.adjust
                        checked: Viewer3DSettings.displayGizmo
                        ToolTip.text: "Display Trackball"
                        onClicked: Viewer3DSettings.displayGizmo = !Viewer3DSettings.displayGizmo
                    }
                    MaterialToolButton {
                        text: MaterialIcons.call_merge
                        ToolTip.text: "Display Origin"
                        checked: Viewer3DSettings.displayOrigin
                        onClicked: Viewer3DSettings.displayOrigin = !Viewer3DSettings.displayOrigin
                    }
                    MaterialToolButton {
                        text: MaterialIcons.light_mode
                        ToolTip.text: "Display Light Controller"
                        checked: Viewer3DSettings.displayLightController
                        onClicked: Viewer3DSettings.displayLightController = !Viewer3DSettings.displayLightController
                    }
                }
                MaterialLabel {
                    text: MaterialIcons.grain
                    padding: 2
                    visible: displayGroup.expanded
                }
                RowLayout {
                    visible: displayGroup.expanded
                    Slider {
                        Layout.fillWidth: true; from: 0; to: 5; stepSize: 0.001
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
                MaterialLabel {
                    text: MaterialIcons.videocam
                    padding: 2
                    visible: displayGroup.expanded
                }
                Slider {
                    visible: displayGroup.expanded
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
            }
        }

        ExpandableGroup {
            id: cameraGroup
            Layout.fillWidth: true
            title: "CAMERA"

            ColumnLayout {
                width: parent.width

                // Image/Camera synchronization
                Flow {
                    Layout.fillWidth: true
                    visible: cameraGroup.expanded
                    spacing: 2

                    // Synchronization
                    MaterialToolButton {
                        id: syncViewpointCamera
                        enabled: _reconstruction && mediaLibrary.count > 0 ? _reconstruction.sfmReport : false
                        text: MaterialIcons.linked_camera
                        ToolTip.text: "View Through The Active Camera"
                        checkable: true
                        checked: enabled && Viewer3DSettings.syncViewpointCamera
                        onCheckedChanged: Viewer3DSettings.syncViewpointCamera = !Viewer3DSettings.syncViewpointCamera
                    }

                    // Image Overlay controls
                    RowLayout {
                        visible: syncViewpointCamera.enabled && Viewer3DSettings.syncViewpointCamera
                        spacing: 2
                        // Activation
                        MaterialToolButton {
                            text: MaterialIcons.image
                            ToolTip.text: "Image Overlay"
                            checked: Viewer3DSettings.viewpointImageOverlay
                            onClicked: Viewer3DSettings.viewpointImageOverlay = !Viewer3DSettings.viewpointImageOverlay
                        }
                        // Opacity
                        Slider {
                            visible: Viewer3DSettings.showViewpointImageOverlay
                            implicitWidth: 60
                            from: 0
                            to: 100
                            value: Viewer3DSettings.viewpointImageOverlayOpacity * 100
                            onValueChanged: Viewer3DSettings.viewpointImageOverlayOpacity = value / 100
                            ToolTip.text: "Image Opacity: " + Viewer3DSettings.viewpointImageOverlayOpacity.toFixed(2)
                            ToolTip.visible: hovered || pressed
                            ToolTip.delay: 100
                        }
                    }
                    // Image Frame control
                    MaterialToolButton {
                        visible: syncViewpointCamera.enabled && Viewer3DSettings.showViewpointImageOverlay
                        enabled: Viewer3DSettings.syncViewpointCamera
                        text: MaterialIcons.crop_free
                        ToolTip.text: "Frame Overlay"
                        checked: Viewer3DSettings.viewpointImageFrame
                        onClicked: Viewer3DSettings.viewpointImageFrame = !Viewer3DSettings.viewpointImageFrame
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    visible: cameraGroup.expanded

                    RowLayout {
                        Layout.fillHeight: true
                        spacing: 2

                        MaterialToolButton {
                            id: resectionIdButton
                            text: MaterialIcons.switch_video
                            ToolTip.text: "Timeline Of Camera Reconstruction Groups"
                            ToolTip.visible: hovered
                            enabled: Viewer3DSettings.resectionIdCount
                            checked: enabled && Viewer3DSettings.displayResectionIds
                            onClicked: {
                                Viewer3DSettings.displayResectionIds = !Viewer3DSettings.displayResectionIds
                                Viewer3DSettings.resectionId = Viewer3DSettings.resectionIdCount
                                resectionIdSlider.value = Viewer3DSettings.resectionId
                            }

                            onEnabledChanged: {
                                Viewer3DSettings.resectionId = Viewer3DSettings.resectionIdCount
                                resectionIdSlider.value = Viewer3DSettings.resectionId
                                if (!enabled) {
                                    Viewer3DSettings.displayResectionIds = false
                                }
                            }
                        }

                        Slider {
                            id: resectionIdSlider
                            value: Viewer3DSettings.resectionId
                            from: 0
                            to: Viewer3DSettings.resectionIdCount
                            stepSize: 1
                            onMoved: Viewer3DSettings.resectionId = value
                            Layout.fillWidth: true
                            leftPadding: 2
                            rightPadding: 2
                            visible: Viewer3DSettings.displayResectionIds
                        }

                        Label {
                            text: resectionIdSlider.value + "/" + Viewer3DSettings.resectionIdCount
                            color: palette.text
                            visible: Viewer3DSettings.displayResectionIds
                        }
                    }

                    RowLayout {
                        spacing: 10
                        Layout.fillWidth: true
                        Layout.margins: 2
                        Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter

                        MaterialToolLabel {
                            iconText: MaterialIcons.stop
                            label.text: {
                                var id = undefined
                                // Ensure there are entries in resectionGroups and a valid resectionId before accessing anything
                                if (Viewer3DSettings.resectionId !== undefined && Viewer3DSettings.resectionGroups &&
                                    Viewer3DSettings.resectionGroups.length > 0)
                                    id = Math.min(Viewer3DSettings.resectionId, Viewer3DSettings.resectionIdCount)
                                if (id !== undefined && Viewer3DSettings.resectionGroups[id] !== undefined)
                                    return Viewer3DSettings.resectionGroups[id]
                                return 0

                            }
                            labelIconColor: palette.text
                            ToolTip.text: "Number Of Cameras In Current Resection Group"
                            visible: Viewer3DSettings.displayResectionIds
                        }

                        MaterialToolLabel {
                            iconText: MaterialIcons.auto_awesome_motion
                            label.text: {
                                let currentCameras = 0
                                if (Viewer3DSettings.resectionGroups) {
                                    for (let i = 0; i <= Viewer3DSettings.resectionIdCount; i++) {
                                        if (i <= Viewer3DSettings.resectionId)
                                            currentCameras += Viewer3DSettings.resectionGroups[i]
                                    }
                                }

                                return currentCameras
                            }
                            labelIconColor: palette.text
                            ToolTip.text: "Number Of Cumulated Cameras"
                            visible: Viewer3DSettings.displayResectionIds
                        }

                        MaterialToolLabel {
                            iconText: MaterialIcons.videocam
                            label.text: {
                                let totalCameras = 0
                                if (Viewer3DSettings.resectionGroups) {
                                    for (let i = 0; i <= Viewer3DSettings.resectionIdCount; i++) {
                                        totalCameras += Viewer3DSettings.resectionGroups[i]
                                    }
                                }

                                return totalCameras
                            }
                            labelIconColor: palette.text
                            ToolTip.text: "Total Number Of Cameras"
                            visible: Viewer3DSettings.displayResectionIds
                        }
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
            }

            ColumnLayout {
                anchors.fill: parent

                SearchBar {
                    id: searchBar
                    Layout.minimumWidth: 150
                    Layout.fillWidth: true
                    Layout.rightMargin: 10
                    Layout.leftMargin: 10
                }

                ListView {
                    id: mediaListView
                    Layout.fillHeight: true
                    Layout.fillWidth: true
                    clip: true
                    spacing: 4

                    ScrollBar.vertical: MScrollBar { id: scrollBar }

                    onCountChanged: {
                        if (mediaListView.count === 0) {
                            Viewer3DSettings.resectionIdCount = 0
                        }
                    }

                    currentIndex: -1

                    Connections {
                        target: uigraph
                        function onSelectedNodeChanged() {
                            mediaListView.currentIndex = -1
                        }
                    }

                    Connections {
                        target: mediaLibrary
                        function onLoadRequest(idx) {
                            mediaListView.positionViewAtIndex(idx, ListView.Visible)
                        }
                    }

                    model: SortFilterDelegateModel {
                        model: mediaLibrary.model
                        sortRole: ""
                        filters: [{role: "label", value: searchBar.text}]
                        delegate: MouseArea {
                            id: mediaDelegate
                            // Add mediaLibrary.count in the binding to ensure 'entity'
                            // is re-evaluated when mediaLibrary delegates are modified
                            property bool loading: model.status === SceneLoader.Loading
                            property bool hovered: model.attribute ? (uigraph ? uigraph.hoveredNode === model.attribute.node : false) : containsMouse
                            property bool isSelectedNode: model.attribute ? (uigraph ? uigraph.selectedNode === model.attribute.node : false) : false

                            onIsSelectedNodeChanged: updateCurrentIndex()

                            function updateCurrentIndex() {
                                if (isSelectedNode) {
                                    mediaListView.currentIndex = index
                                }

                                // If the index is updated, and the resection ID count is available, update every resection-related variable:
                                // this covers the changes of index that occur when a node whose output is already loaded in the 3D viewer is
                                // clicked/double-clicked, and when the active entry is removed from the list.
                                if (model.resectionIdCount) {
                                    Viewer3DSettings.resectionIdCount = model.resectionIdCount
                                    Viewer3DSettings.resectionGroups = model.resectionGroups
                                    Viewer3DSettings.resectionId = model.resectionId
                                    resectionIdSlider.value = model.resectionId
                                }
                            }

                            height: childrenRect.height
                            width: {
                                if (parent != null)
                                    return parent.width - scrollBar.width
                                return undefined
                            }

                            hoverEnabled: true
                            onEntered: {
                                if (model.attribute)
                                    uigraph.hoveredNode = model.attribute.node
                            }
                            onExited: {
                                if (model.attribute)
                                    uigraph.hoveredNode = null
                            }
                            onClicked: function(mouse) {
                                if (model.attribute)
                                    uigraph.selectedNode = model.attribute.node
                                else
                                    uigraph.selectedNode = null
                                if (mouse.button == Qt.RightButton)
                                    contextMenu.popup()
                                mediaListView.currentIndex = index

                                // Update the resection ID-related objects based on the active model
                                Viewer3DSettings.resectionIdCount = model.resectionIdCount
                                Viewer3DSettings.resectionGroups = model.resectionGroups
                                Viewer3DSettings.resectionId = model.resectionId
                                resectionIdSlider.value = model.resectionId
                            }
                            onDoubleClicked: {
                                model.visible = true;
                                nodeActivated(model.attribute.node);
                            }

                            Connections {
                                target: resectionIdSlider
                                function onValueChanged() {
                                    model.resectionId = resectionIdSlider.value
                                }
                            }

                            RowLayout {
                                width: parent.width
                                spacing: 2

                                property string src: model.source
                                onSrcChanged: focusAnim.restart()

                                Connections {
                                    target: mediaListView
                                    function onCountChanged() {
                                        mediaDelegate.updateCurrentIndex()
                                    }
                                }

                                // Current/selected element indicator
                                Rectangle {
                                    Layout.fillHeight: true
                                    width: 2
                                    color: {
                                        if (mediaListView.currentIndex == index || mediaDelegate.isSelectedNode)
                                            return label.palette.highlight;
                                        if (mediaDelegate.hovered)
                                            return Qt.darker(label.palette.highlight, 1.5);
                                        return "transparent";
                                    }
                                }

                                // Media visibility/loading control
                                MaterialToolButton {
                                    Layout.alignment: Qt.AlignTop
                                    Layout.fillHeight: true
                                    text: model.visible ? MaterialIcons.visibility : MaterialIcons.visibility_off
                                    font.pointSize: 10
                                    ToolTip.text: model.visible ? "Hide" : model.requested ? "Show" : model.valid ? "Load and Show" : "Load and Show when Available"
                                    flat: true
                                    opacity: model.visible ? 1.0 : 0.6
                                    onClicked: {
                                        if (hoverArea.modifiers & Qt.ControlModifier)
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
                                        onPositionChanged: function(mouse) {
                                            modifiers = mouse.modifiers
                                        }
                                        onExited: modifiers = Qt.NoModifier
                                        onPressed: function(mouse) {
                                            modifiers = mouse.modifiers;
                                            mouse.accepted = false;
                                        }
                                    }
                                }

                                // BoundingBox visibility (if meshing node)
                                MaterialToolButton {
                                    visible: model.hasBoundingBox
                                    enabled: model.visible
                                    Layout.alignment: Qt.AlignTop
                                    Layout.fillHeight: true
                                    text: MaterialIcons.transform_
                                    font.pointSize: 10
                                    ToolTip.text: model.displayBoundingBox ? "Hide BBox" : "Show BBox"
                                    flat: true
                                    opacity: model.visible ? (model.displayBoundingBox ? 1.0 : 0.6) : 0.6
                                    onClicked: {
                                        model.displayBoundingBox = !model.displayBoundingBox
                                    }
                                }

                                // Transform visibility (if SfMTransform node)
                                MaterialToolButton {
                                    visible: model.hasTransform
                                    enabled: model.visible
                                    Layout.alignment: Qt.AlignTop
                                    Layout.fillHeight: true
                                    text: MaterialIcons._3d_rotation
                                    font.pointSize: 10
                                    ToolTip.text: model.displayTransform ? "Hide Gizmo" : "Show Gizmo"
                                    flat: true
                                    opacity: model.visible ? (model.displayTransform ? 1.0 : 0.6) : 0.6
                                    onClicked: {
                                        model.displayTransform = !model.displayTransform
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
                                            color: palette.text
                                            opacity: model.valid ? 1.0 : 0.6
                                            elide: Text.ElideMiddle
                                            font.weight: mediaListView.currentIndex === index ? Font.DemiBold : Font.Normal
                                            background: Rectangle {
                                                Connections {
                                                    target: mediaLibrary
                                                    function onLoadRequest(idx) {
                                                        if (idx === index)
                                                            focusAnim.restart()
                                                    }
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
                                            Flow {
                                                width: parent.width
                                                spacing: 4
                                                visible: model.status === SceneLoader.Ready
                                                RowLayout {
                                                    spacing: 1
                                                    visible: model.vertexCount
                                                    MaterialLabel { text: MaterialIcons.grain }
                                                    Label {
                                                        text: Format.intToString(model.vertexCount)
                                                        color: palette.text
                                                    }
                                                }
                                                RowLayout {
                                                    spacing: 1
                                                    visible: model.faceCount
                                                    MaterialLabel { text: MaterialIcons.details; rotation: -180 }
                                                    Label {
                                                        text: Format.intToString(model.faceCount)
                                                        color: palette.text
                                                    }
                                                }
                                                RowLayout {
                                                    spacing: 1
                                                    visible: model.cameraCount
                                                    MaterialLabel { text: MaterialIcons.videocam }
                                                    Label {
                                                        text: model.cameraCount
                                                        color: palette.text
                                                    }
                                                }
                                                RowLayout {
                                                    spacing: 1
                                                    visible: model.textureCount
                                                    MaterialLabel { text: MaterialIcons.texture }
                                                    Label {
                                                        text: model.textureCount
                                                        color: palette.text
                                                    }
                                                }
                                            }
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
                                            onTriggered: Clipboard.setText(Filepath.normpath(model.source))
                                        }
                                        MenuSeparator {}
                                        MenuItem {
                                            text: model.requested ? "Unload Media" : "Load Media"
                                            enabled: model.valid
                                            onTriggered: model.requested = !model.requested
                                        }
                                    }
                                }

                                // Remove media from library button
                                MaterialToolButton {
                                    id: removeButton
                                    Layout.alignment: Qt.AlignTop
                                    Layout.fillHeight: true

                                    visible: !loading && mediaDelegate.containsMouse
                                    text: MaterialIcons.clear
                                    font.pointSize: 10

                                    ToolTip.text: "Remove"
                                    ToolTip.delay: 500
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
        }
    }
}
