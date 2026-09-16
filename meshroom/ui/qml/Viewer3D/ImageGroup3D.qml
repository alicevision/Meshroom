import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Controls 1.0
import MaterialIcons 2.2
import Utils 1.0

ExpandableGroup {
    id: root

    property var collection: null

    function imageLayer() {
        if (!root.collection || !root.collection.sceneView)
        {
            return null
        }

        return root.collection.sceneView.imageLayerRef
    }

    function imageLayerVisible() {
        var layer = imageLayer()
        return layer ? layer.visible : false
    }

    function setImageLayerVisible(value) {
        var layer = imageLayer()
        if (layer)
        {
            layer.visible = value
        }
    }

    function imageLayerSource() {
        var layer = imageLayer()
        if (layer && layer.source !== undefined)
        {
            return layer.source
        }

        return ""
    }

    function closeImageLayer() {
        var layer = imageLayer()
        if (!layer)
        {
            return
        }

        layer.visible = false
        if (layer.source !== undefined)
        {
            layer.source = ""
        }
    }

    Layout.fillWidth: true
    title: "Image Layer"

    Component.onCompleted: expanded = true

    RowLayout {
        visible: root.expanded
        width: parent.width
        spacing: 4

        Item {
            width: 2
            Layout.fillHeight: true
        }

        BusyIndicator {
            visible: {
                if (imageLayer())
                {
                    if (imageLayer().loading)
                    {
                        return true
                    }
                } 
                return false
            }
            running: visible
            padding: 0
            implicitWidth: 12
            implicitHeight: 12
            Layout.alignment: Qt.AlignVCenter
        }

        MaterialToolButton {
            visible: !imageLayer() || !imageLayer().loading
            text: MaterialIcons.clear
            font.pointSize: 10
            ToolTip.text: "Close"
            ToolTip.delay: 500
            onClicked: {
                root.closeImageLayer()
                imageVisibilityButton.rowVisible = false
            }
        }

        Label {
            Layout.fillWidth: true
            text: {
                var source = root.imageLayerSource()
                return source ? Filepath.basename(source) : "No image"
            }
            color: palette.text
            elide: Text.ElideMiddle
            topPadding: 3
            bottomPadding: topPadding
            ToolTip.text: root.imageLayerSource()
            ToolTip.visible: labelMouseArea.containsMouse && ToolTip.text.length > 0
            ToolTip.delay: 300

            MouseArea {
                id: labelMouseArea
                anchors.fill: parent
                hoverEnabled: true
                acceptedButtons: Qt.NoButton
            }
        }

        MaterialToolButton {
            id: imageVisibilityButton
            property bool rowVisible: root.imageLayerVisible()
            text: rowVisible ? MaterialIcons.visibility : MaterialIcons.visibility_off
            font.pointSize: 10
            flat: true
            opacity: rowVisible ? 1.0 : 0.6
            ToolTip.text: rowVisible ? "Visible" : "Hidden"
            onClicked: {
                var nextValue = !rowVisible
                root.setImageLayerVisible(nextValue)
                rowVisible = nextValue
            }

            Connections {
                target: root

                function onCollectionChanged() {
                    parent.rowVisible = root.imageLayerVisible()
                }
            }
        }
    }
}
