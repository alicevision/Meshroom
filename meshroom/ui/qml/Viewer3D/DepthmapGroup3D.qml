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

        return root.collection.depthmapLayerAt(index)
    }

    function layerVisible(index) {
        var layer = layerAt(index)
        return layer ? layer.visible : true
    }

    function setLayerVisible(index, value) {
        var layer = layerAt(index)
        if (layer)
        {
            layer.visible = value
        }
    }


    Layout.fillWidth: true
    Layout.fillHeight: true
    title: "Depthmaps (" + (collection ? collection.depthmapModel.count : 0) + ")"

    Component.onCompleted: expanded = true

    ColumnLayout {
        anchors.fill: parent
        spacing: 2

        ListView {
            id: depthmapListView
            visible: root.expanded
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.preferredHeight: Math.min(contentHeight, 220)
            clip: true
            spacing: 4

            ScrollBar.vertical: MScrollBar { id: depthmapScrollBar }

            model: collection ? collection.depthmapModel : null

            delegate: MouseArea {
                    id: depthmapDelegate
                    hoverEnabled: true
                    property int advancedLabelWidth: 70
                    property bool rowLoading: {
                        var object = root.layerAt(index)
                        return object && object.loading === true
                    }
                    property bool rowVisible: root.layerVisible(index)

                    onRowVisibleChanged: {
                        root.setLayerVisible(index, rowVisible)
                    }


                    width: parent ? parent.width - depthmapScrollBar.width : 0
                    height: rowContent.implicitHeight

                    onClicked: function() {
                        depthmapListView.currentIndex = index
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
                                    if (depthmapListView.currentIndex === index)
                                        return palette.highlight
                                    if (depthmapDelegate.containsMouse)
                                        return Qt.darker(palette.highlight, 1.5)
                                    return "transparent"
                                }
                            }

                            BusyIndicator {
                                visible: depthmapDelegate.rowLoading
                                running: visible
                                padding: 0
                                implicitWidth: 12
                                implicitHeight: 12
                                Layout.alignment: Qt.AlignVCenter
                            }

                            MaterialToolButton {
                                visible: !depthmapDelegate.rowLoading
                                text: MaterialIcons.clear
                                font.pointSize: 10
                                ToolTip.text: "Remove"
                                ToolTip.delay: 500
                                onClicked: collection.removeDepthmap(index)
                            }

                            Label {
                                Layout.fillWidth: true
                                text: label && label.length > 0 ? label : Inspector3DUtils.randomLabel(index, "Mesh")
                                color: palette.text
                                elide: Text.ElideMiddle
                                font.weight: depthmapListView.currentIndex === index ? Font.DemiBold : Font.Normal
                                topPadding: 3
                                bottomPadding: topPadding
                            }

                            MaterialToolButton {
                                text: depthmapDelegate.rowVisible ? MaterialIcons.visibility : MaterialIcons.visibility_off
                                font.pointSize: 10
                                flat: true
                                opacity: depthmapDelegate.rowVisible ? 1.0 : 0.6
                                ToolTip.text: depthmapDelegate.rowVisible ? "Visible" : "Hidden"
                                onClicked: depthmapDelegate.rowVisible = !depthmapDelegate.rowVisible
                            }
                        }
                    }
            }

            Label {
                anchors.centerIn: parent
                visible: collection && collection.depthmapModel.count === 0
                text: "No depthmap entries"
                color: palette.mid
            }
        }
    }
}
