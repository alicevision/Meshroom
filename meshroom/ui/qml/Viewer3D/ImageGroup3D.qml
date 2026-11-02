import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Controls 1.0
import MaterialIcons 2.2
import Utils 1.0

ExpandableGroup {
    id: root

    property var collection: null
    readonly property var imageLayer: collection && collection.sceneView ? collection.sceneView.imageLayerRef : null
    readonly property string source: imageLayer && imageLayer.source !== undefined ? imageLayer.source : ""

    Layout.fillWidth: true
    title: "Image Layer"

    Component.onCompleted: expanded = true

    RowLayout {
        visible: root.expanded
        width: parent.width
        spacing: 4

        LoadingRemoveButton {
            Layout.leftMargin: 6
            loading: root.imageLayer ? root.imageLayer.loading === true : false
            toolTip: "Close"
            onRemoveRequested: {
                root.imageLayer.visible = false
                root.imageLayer.source = ""
            }
        }

        Label {
            Layout.fillWidth: true
            text: root.source ? Filepath.basename(root.source) : "No image"
            color: palette.text
            elide: Text.ElideMiddle
            topPadding: 3
            bottomPadding: topPadding
            ToolTip.text: root.source
            ToolTip.visible: labelMouseArea.containsMouse && ToolTip.text.length > 0
            ToolTip.delay: 300

            MouseArea {
                id: labelMouseArea
                anchors.fill: parent
                hoverEnabled: true
                acceptedButtons: Qt.NoButton
            }
        }

        ToggleIconButton {
            enabled: root.imageLayer !== null
            active: root.imageLayer ? root.imageLayer.visible : false
            activeIcon: MaterialIcons.visibility
            inactiveIcon: MaterialIcons.visibility_off
            activeToolTip: "Visible"
            inactiveToolTip: "Hidden"
            onClicked: root.imageLayer.visible = !root.imageLayer.visible
        }
    }
}
