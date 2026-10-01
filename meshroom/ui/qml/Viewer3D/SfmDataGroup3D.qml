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

        return root.collection.sfmDataLayerAt(index)
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

    function sfmDataObjectAt(index) {
        if (!root.collection)
        {
            return null
        }

        return root.collection.sfmDataObjectAt(index)
    }

    function sfmDataMaxResectionId(index, fallbackValue) {
        var sfmDataObject = sfmDataObjectAt(index)
        if (!sfmDataObject)
        {
            return fallbackValue
        }

        if (sfmDataObject.maxResectionId !== undefined)
        {
            return sfmDataObject.maxResectionId
        }

        return fallbackValue
    }

    function sfmDataLimitResectionId(index, fallbackValue) {
        var sfmDataObject = sfmDataObjectAt(index)
        if (!sfmDataObject)
        {
            return fallbackValue
        }

        if (sfmDataObject.limitResectionId !== undefined)
        {
            return sfmDataObject.limitResectionId
        }

        return fallbackValue
    }

    function setSfmDataLimitResectionId(index, value) {
        var sfmDataObject = sfmDataObjectAt(index)
        if (!sfmDataObject)
        {
            return
        }

        if (sfmDataObject.limitResectionId !== undefined)
        {
            sfmDataObject.limitResectionId = Math.round(value)
        }
    }

    function layerCameraSize(index, fallbackValue) {
        var layer = layerAt(index)
        if (layer && layer.cameraSize !== undefined)
        {
            return layer.cameraSize
        }

        return fallbackValue
    }

    function setLayerCameraSize(index, value) {
        var layer = layerAt(index)
        if (layer && layer.cameraSize !== undefined)
        {
            layer.cameraSize = value
        }
    }

    function layerPointSize(index, fallbackValue) {
        var layer = layerAt(index)
        if (!layer)
        {
            return fallbackValue
        }

        if (layer.pointSize !== undefined)
        {
            return layer.pointSize
        }

        return fallbackValue
    }

    function setLayerPointSize(index, value) {
        var layer = layerAt(index)
        if (!layer)
        {
            return
        }

        if (layer.pointSize !== undefined)
        {
            layer.pointSize = value
        }
    }

    Layout.fillWidth: true
    Layout.fillHeight: true
    title: "Sfm data (" + (collection ? collection.sfmDataModel.count : 0) + ")"

    Component.onCompleted: expanded = true

    ColumnLayout {
        anchors.fill: parent
        spacing: 2

        ListView {
            id: sfmDataListView
            visible: root.expanded
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.preferredHeight: Math.min(contentHeight, 220)
            clip: true
            spacing: 4

            ScrollBar.vertical: MScrollBar { id: sfmDataScrollBar }

            model: collection ? collection.sfmDataModel : null

            delegate: MouseArea {
                id: sfmDataDelegate
                hoverEnabled: true
                property bool rowLoading: {
                    var object = root.sfmDataObjectAt(index)
                    return object && object.loading === true
                }
                property bool rowVisible: root.layerVisible(index)
                property bool rowPickable: root.layerPicking(index)
                property bool rowExpanded: false
                property real rowMaxResectionId: root.sfmDataMaxResectionId(index, 100)

                onRowVisibleChanged: {
                    root.setLayerVisible(index, rowVisible)
                }
                onRowPickableChanged: {
                    root.setLayerPicking(index, rowPickable)
                }

                width: parent ? parent.width - sfmDataScrollBar.width : 0
                height: rowContent.implicitHeight

                onClicked: function() {
                    sfmDataListView.currentIndex = index
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
                                if (sfmDataListView.currentIndex === index)
                                    return palette.highlight
                                if (sfmDataDelegate.containsMouse)
                                    return Qt.darker(palette.highlight, 1.5)
                                return "transparent"
                            }
                        }

                        BusyIndicator {
                            visible: sfmDataDelegate.rowLoading
                            running: visible
                            padding: 0
                            implicitWidth: 12
                            implicitHeight: 12
                            Layout.alignment: Qt.AlignVCenter
                        }

                        MaterialToolButton {
                            visible: !sfmDataDelegate.rowLoading
                            text: MaterialIcons.clear
                            font.pointSize: 10
                            ToolTip.text: "Remove"
                            ToolTip.delay: 500
                            onClicked: collection.removeSfmData(index)
                        }

                        Label {
                            Layout.fillWidth: true
                            text: label && label.length > 0 ? label : Inspector3DUtils.randomLabel(index, "SfmData")
                            color: palette.text
                            elide: Text.ElideMiddle
                            font.weight: sfmDataListView.currentIndex === index ? Font.DemiBold : Font.Normal
                            topPadding: 3
                            bottomPadding: topPadding
                        }

                        MaterialToolButton {
                            text: sfmDataDelegate.rowVisible ? MaterialIcons.visibility : MaterialIcons.visibility_off
                            font.pointSize: 10
                            flat: true
                            opacity: sfmDataDelegate.rowVisible ? 1.0 : 0.6
                            ToolTip.text: sfmDataDelegate.rowVisible ? "Visible" : "Hidden"
                            onClicked: sfmDataDelegate.rowVisible = !sfmDataDelegate.rowVisible
                        }

                        MaterialToolButton {
                            text: MaterialIcons.touch_app
                            font.pointSize: 10
                            flat: true
                            opacity: sfmDataDelegate.rowPickable ? 1.0 : 0.6
                            ToolTip.text: sfmDataDelegate.rowPickable ? "Pickable" : "Not Pickable"
                            onClicked: sfmDataDelegate.rowPickable = !sfmDataDelegate.rowPickable
                        }

                        MaterialToolButton {
                            enabled: !sfmDataDelegate.rowLoading
                            text: sfmDataDelegate.rowExpanded ? MaterialIcons.keyboard_arrow_down : MaterialIcons.keyboard_arrow_right
                            font.pointSize: 10
                            flat: true
                            ToolTip.text: sfmDataDelegate.rowExpanded ? "Hide Advanced" : "Show Advanced"
                            onClicked: sfmDataDelegate.rowExpanded = !sfmDataDelegate.rowExpanded
                        }
                    }

                    RowLayout {
                        visible: sfmDataDelegate.rowExpanded
                        width: parent.width
                        spacing: 2

                        Item {
                            width: 12
                            Layout.fillHeight: true
                        }

                        MaterialLabel {
                            text: MaterialIcons.switch_video
                            padding: 2
                        }

                        Slider {
                            Layout.fillWidth: true
                            from: 0
                            to: rowMaxResectionId
                            stepSize: 1
                            value: root.sfmDataLimitResectionId(index, rowMaxResectionId)
                            onMoved: root.setSfmDataLimitResectionId(index, value)
                            ToolTip.text: "ResectionId: " + value.toFixed(0)
                            ToolTip.visible: hovered || pressed
                            ToolTip.delay: 100
                        }

                        Label {
                            text: root.sfmDataLimitResectionId(index, rowMaxResectionId).toFixed(0)
                            color: palette.text
                        }

                        Item {
                            width: 8
                            Layout.fillHeight: true
                        }
                    }

                    RowLayout {
                        visible: sfmDataDelegate.rowExpanded
                        width: parent.width
                        spacing: 2

                        Item {
                            width: 12
                            Layout.fillHeight: true
                        }

                        MaterialLabel {
                            text: MaterialIcons.videocam
                            padding: 2
                        }

                        Slider {
                            Layout.fillWidth: true
                            from: 0
                            to: 2
                            stepSize: 0.01
                            value: root.layerCameraSize(index, 1.0)
                            onMoved: root.setLayerCameraSize(index, value)
                            ToolTip.text: "Camera Scale: " + value.toFixed(2)
                            ToolTip.visible: hovered || pressed
                            ToolTip.delay: 100
                        }

                        Label {
                            text: root.layerCameraSize(index, 1.0).toFixed(2)
                            color: palette.text
                        }

                        Item {
                            width: 8
                            Layout.fillHeight: true
                        }
                    }

                    RowLayout {
                        visible: sfmDataDelegate.rowExpanded
                        width: parent.width
                        spacing: 2

                        Item {
                            width: 12
                            Layout.fillHeight: true
                        }

                        MaterialLabel {
                            text: MaterialIcons.center_focus_strong
                            padding: 2
                        }

                        Slider {
                            Layout.fillWidth: true
                            from: 0
                            to: 10
                            stepSize: 0.01
                            value: root.layerPointSize(index, 1.0)
                            onMoved: root.setLayerPointSize(index, value)
                            ToolTip.text: "Point Size: " + value.toFixed(2)
                            ToolTip.visible: hovered || pressed
                            ToolTip.delay: 100
                        }

                        Label {
                            text: root.layerPointSize(index, 1.0).toFixed(2)
                            color: palette.text
                        }

                        Item {
                            width: 8
                            Layout.fillHeight: true
                        }
                    }

                    RowLayout {
                        visible: sfmDataDelegate.rowExpanded
                        width: parent.width
                        spacing: 2

                        Item {
                            width: 12
                            Layout.fillHeight: true
                        }

                        CheckBox {
                            text: "View through camera"
                            font.pointSize: 10
                            checked: false

                            onClicked: {

                                if (!collection)
                                {
                                    return
                                }


                                collection.setSelectedSfmDataObject(checked?root.sfmDataObjectAt(index):null)
                            }
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
                visible: collection && collection.sfmDataModel.count === 0
                text: "No sfmData entries"
                color: palette.mid
            }
        }
    }
}
