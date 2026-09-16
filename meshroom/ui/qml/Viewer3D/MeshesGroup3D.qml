import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "Inspector3DUtils.js" as Inspector3DUtils

import Controls 1.0
import MaterialIcons 2.2

ExpandableGroup {
    id: root

    property var collection: null

    function layerAt(index) {
        if (!root.collection)
        {
            return null
        }

        return root.collection.meshLayerAt(index)
    }

    function layerVisible(index) {
        var layer = layerAt(index)
        return layer ? layer.visible : true
    }

    function layerPicking(index) {
        var layer = layerAt(index)
        return layer ? layer.picking : true
    }

    function setLayerVisible(index, value) {
        var layer = layerAt(index)
        if (layer)
        {
            layer.visible = value
        }
    }

    function setLayerPicking(index, value) {
        var layer = layerAt(index)
        if (layer)
        {
            layer.picking = value
        }
    }

    function layerShadingMode(index, fallbackValue) {
        var layer = layerAt(index)
        if (layer && layer.shadingMode !== undefined)
        {
            return layer.shadingMode
        }

        return fallbackValue
    }

    function setLayerShadingMode(index, value) {
        var layer = layerAt(index)
        if (layer && layer.shadingMode !== undefined)
        {
            layer.shadingMode = value
        }
    }

    function layerWireframeMode(index, fallbackValue) {
        var layer = layerAt(index)
        if (layer && layer.wireframeMode !== undefined)
        {
            return layer.wireframeMode
        }

        return fallbackValue
    }

    function layerOpacity(index, fallbackValue) {
        var layer = layerAt(index)
        if (layer && layer.opacity !== undefined)
        {
            return layer.opacity
        }

        return fallbackValue
    }

    function meshObjectAt(index) {
        if (!root.collection)
        {
            return null
        }

        return root.collection.meshObjectAt(index)
    }

    function setLayerWireframeMode(index, value) {
        var layer = layerAt(index)
        if (layer && layer.wireframeMode !== undefined)
        {
            layer.wireframeMode = value
        }
    }

    function setLayerOpacity(index, value) {
        var layer = layerAt(index)
        if (layer && layer.opacity !== undefined)
        {
            layer.opacity = value
        }
    }

    Layout.fillWidth: true
    Layout.fillHeight: true
    title: "Meshes (" + (collection ? collection.meshModel.count : 0) + ")"

    Component.onCompleted: expanded = true

    ColumnLayout {
        anchors.fill: parent
        spacing: 2

        ListView {
            id: meshListView
            visible: root.expanded
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.preferredHeight: Math.min(contentHeight, 220)
            clip: true
            spacing: 4

            ScrollBar.vertical: MScrollBar { id: meshScrollBar }

            model: collection ? collection.meshModel : null

            delegate: MouseArea {
                    id: meshDelegate
                    hoverEnabled: true
                    property int advancedLabelWidth: 70
                    property bool rowLoading: {
                        var object = root.meshObjectAt(index)
                        return object && object.loading === true
                    }
                    property bool rowVisible: root.layerVisible(index)
                    property bool rowPickable: root.layerPicking(index)
                    property bool rowExpanded: false

                    onRowVisibleChanged: {
                        root.setLayerVisible(index, rowVisible)
                    }
                    onRowPickableChanged: {
                        root.setLayerPicking(index, rowPickable)
                    }

                    width: parent ? parent.width - meshScrollBar.width : 0
                    height: rowContent.implicitHeight

                    onClicked: function() {
                        meshListView.currentIndex = index
                    }

                    ColumnLayout {
                        id: rowContent
                        width: parent.width
                        spacing: 3

                        RowLayout {
                            width: parent.width
                            spacing: 4

                            Rectangle {
                                Layout.fillHeight: true
                                width: 2
                                color: {
                                    if (meshListView.currentIndex === index)
                                        return palette.highlight
                                    if (meshDelegate.containsMouse)
                                        return Qt.darker(palette.highlight, 1.5)
                                    return "transparent"
                                }
                            }

                            BusyIndicator {
                                visible: meshDelegate.rowLoading
                                running: visible
                                padding: 0
                                implicitWidth: 12
                                implicitHeight: 12
                                Layout.alignment: Qt.AlignVCenter
                            }

                            MaterialToolButton {
                                visible: !meshDelegate.rowLoading
                                text: MaterialIcons.clear
                                font.pointSize: 10
                                ToolTip.text: "Remove"
                                ToolTip.delay: 500
                                onClicked: collection.removeMesh(index)
                            }

                            Label {
                                Layout.fillWidth: true
                                text: label && label.length > 0 ? label : Inspector3DUtils.randomLabel(index, "Mesh")
                                color: palette.text
                                elide: Text.ElideMiddle
                                font.weight: meshListView.currentIndex === index ? Font.DemiBold : Font.Normal
                                topPadding: 3
                                bottomPadding: topPadding
                            }

                            MaterialToolButton {
                                text: meshDelegate.rowVisible ? MaterialIcons.visibility : MaterialIcons.visibility_off
                                font.pointSize: 10
                                flat: true
                                opacity: meshDelegate.rowVisible ? 1.0 : 0.6
                                ToolTip.text: meshDelegate.rowVisible ? "Visible" : "Hidden"
                                onClicked: meshDelegate.rowVisible = !meshDelegate.rowVisible
                            }

                            MaterialToolButton {
                                text: MaterialIcons.touch_app
                                font.pointSize: 10
                                flat: true
                                opacity: meshDelegate.rowPickable ? 1.0 : 0.6
                                ToolTip.text: meshDelegate.rowPickable ? "Pickable" : "Not Pickable"
                                onClicked: meshDelegate.rowPickable = !meshDelegate.rowPickable
                            }

                            MaterialToolButton {
                                enabled: !meshDelegate.rowLoading
                                text: meshDelegate.rowExpanded ? MaterialIcons.keyboard_arrow_down : MaterialIcons.keyboard_arrow_right
                                font.pointSize: 10
                                flat: true
                                ToolTip.text: meshDelegate.rowExpanded ? "Hide Advanced" : "Show Advanced"
                                onClicked: meshDelegate.rowExpanded = !meshDelegate.rowExpanded
                            }
                        }

                        RowLayout {
                            visible: meshDelegate.rowExpanded
                            width: parent.width
                            spacing: 2

                            Item {
                                width: 12
                                Layout.fillHeight: true
                            }

                            Label {
                                text: "Shading"
                                color: palette.text
                                Layout.preferredWidth: meshDelegate.advancedLabelWidth
                            }

                            ComboBox {
                                model: ["Shaded", "Normal"]
                                currentIndex: root.layerShadingMode(index, 0)
                                onActivated: function(comboIndex) {
                                    root.setLayerShadingMode(index, comboIndex)
                                }
                            }

                            Item {
                                width: 8
                                Layout.fillHeight: true
                            }
                        }

                        RowLayout {
                            visible: meshDelegate.rowExpanded
                            width: parent.width
                            spacing: 2

                            Item {
                                width: 12
                                Layout.fillHeight: true
                            }

                            Label {
                                text: "Wireframe"
                                color: palette.text
                                Layout.preferredWidth: meshDelegate.advancedLabelWidth
                            }

                            ComboBox {
                                model: ["Solid", "Solid + Wireframe", "Wireframe"]
                                currentIndex: root.layerWireframeMode(index, 0)
                                onActivated: function(comboIndex) {
                                    root.setLayerWireframeMode(index, comboIndex)
                                }
                            }

                            Item {
                                width: 8
                                Layout.fillHeight: true
                            }
                        }

                        RowLayout {
                            visible: meshDelegate.rowExpanded
                            width: parent.width
                            spacing: 2

                            Item {
                                width: 12
                                Layout.fillHeight: true
                            }

                            Label {
                                text: "Opacity"
                                color: palette.text
                                Layout.preferredWidth: meshDelegate.advancedLabelWidth
                            }

                            Slider {
                                Layout.fillWidth: true
                                from: 0.0
                                to: 1.0
                                stepSize: 0.01
                                value: root.layerOpacity(index, 1.0)
                                onMoved: root.setLayerOpacity(index, value)
                                ToolTip.text: "Opacity: " + value.toFixed(2)
                                ToolTip.visible: hovered || pressed
                                ToolTip.delay: 100
                            }

                            Label {
                                text: root.layerOpacity(index, 1.0).toFixed(2)
                                color: palette.text
                            }

                            Item {
                                width: 8
                                Layout.fillHeight: true
                            }
                        }
                    }
            }

            Label {
                anchors.centerIn: parent
                visible: collection && collection.meshModel.count === 0
                text: "No mesh entries"
                color: palette.mid
            }
        }
    }
}
