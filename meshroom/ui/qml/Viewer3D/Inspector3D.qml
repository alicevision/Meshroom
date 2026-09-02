import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Controls 1.0
import MaterialIcons 2.2
import Utils 1.0

FloatingPane {
    id: root

    implicitWidth: 200
    opaque: true
    property var collection: null

    function randomLabel(index, entryType) {
        var tag = ["Atlas", "Comet", "Echo", "Nimbus", "Quartz", "Vector"]
        return entryType + " " + tag[index % tag.length] + " #" + (index + 1)
    }

    function layerAt(sectionKey, index) {
        if (!root.collection)
        {
            return null
        }

        if (sectionKey === "mesh")
        {
            return root.collection.meshLayerAt(index)
        }

        if (sectionKey === "sfmData")
        {
            return root.collection.sfmDataLayerAt(index)
        }

        return null
    }

    function layerVisible(sectionKey, index) {
        var layer = layerAt(sectionKey, index)
        return layer ? layer.visible : true
    }

    function layerPicking(sectionKey, index) {
        var layer = layerAt(sectionKey, index)
        return layer ? layer.picking : true
    }

    function setLayerVisible(sectionKey, index, value) {
        var layer = layerAt(sectionKey, index)
        if (layer)
        {
            layer.visible = value
        }
    }

    function setLayerPicking(sectionKey, index, value) {
        var layer = layerAt(sectionKey, index)
        if (layer)
        {
            layer.picking = value
        }
    }

    function layerCameraSize(sectionKey, index, fallbackValue) {
        var layer = layerAt(sectionKey, index)
        if (layer && layer.cameraSize !== undefined)
        {
            return layer.cameraSize
        }
        return fallbackValue
    }

    function setLayerCameraSize(sectionKey, index, value) {
        var layer = layerAt(sectionKey, index)
        if (layer && layer.cameraSize !== undefined)
        {
            layer.cameraSize = value
        }
    }

    function layerPointSize(sectionKey, index, fallbackValue) {
        var layer = layerAt(sectionKey, index)
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

    function setLayerPointSize(sectionKey, index, value) {
        var layer = layerAt(sectionKey, index)
        if (!layer)
        {
            return
        }

        if (layer.pointSize !== undefined)
        {
            layer.pointSize = value
        }
    }

    function layerShadingMode(index, fallbackValue) {
        var layer = layerAt("mesh", index)
        if (layer && layer.shadingMode !== undefined)
        {
            return layer.shadingMode
        }

        return fallbackValue
    }

    function setLayerShadingMode(index, value) {
        var layer = layerAt("mesh", index)
        if (layer && layer.shadingMode !== undefined)
        {
            layer.shadingMode = value
        }
    }

    function layerWireframeMode(index, fallbackValue) {
        var layer = layerAt("mesh", index)
        if (layer && layer.wireframeMode !== undefined)
        {
            return layer.wireframeMode
        }

        return fallbackValue
    }

    function setLayerWireframeMode(index, value) {
        var layer = layerAt("mesh", index)
        if (layer && layer.wireframeMode !== undefined)
        {
            layer.wireframeMode = value
        }
    }

    function sfmDataMaxResectionId(index, fallbackValue) {
        if (!root.collection)
        {
            return fallbackValue
        }

        var sfmDataObject = root.collection.sfmDataObjectAt(index)
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
        if (!root.collection)
        {
            return fallbackValue
        }

        var sfmDataObject = root.collection.sfmDataObjectAt(index)
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
        if (!root.collection)
        {
            return
        }

        var sfmDataObject = root.collection.sfmDataObjectAt(index)
        if (!sfmDataObject)
        {
            return
        }

        if (sfmDataObject.limitResectionId !== undefined)
        {
            sfmDataObject.limitResectionId = Math.round(value)
        }
    }

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

        Label {
            text: "Inspector 3D"
            color: palette.text
            font.bold: true
            Layout.fillWidth: true
            leftPadding: 6
            topPadding: 2
        }

        Group {
            title: "3D Objects"
            Layout.fillWidth: true
            Layout.fillHeight: true
            sidePadding: 0

            ColumnLayout {
                anchors.fill: parent
                spacing: 4

                ExpandableGroup {
                    id: meshesGroup
                    Layout.fillWidth: true
                    expanded: true
                    title: "MESHES (" + (root.collection ? root.collection.meshModel.count : 0) + ")"

                    ColumnLayout {
                        width: parent.width
                        spacing: 2

                        ListView {
                            id: meshListView
                            visible: meshesGroup.expanded
                            Layout.fillWidth: true
                            Layout.preferredHeight: Math.min(contentHeight, 220)
                            clip: true
                            spacing: 4

                            ScrollBar.vertical: MScrollBar { id: meshScrollBar }

                            model: root.collection ? root.collection.meshModel : null

                            delegate: MouseArea {
                                    id: meshDelegate
                                    hoverEnabled: true
                                    property bool rowVisible: root.layerVisible("mesh", index)
                                    property bool rowPickable: root.layerPicking("mesh", index)
                                    property bool rowExpanded: false

                                    onRowVisibleChanged: {
                                        root.setLayerVisible("mesh", index, rowVisible)
                                    }
                                    onRowPickableChanged: {
                                        root.setLayerPicking("mesh", index, rowPickable)
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

                                            MaterialToolButton {
                                                text: MaterialIcons.clear
                                                font.pointSize: 10
                                                ToolTip.text: "Remove"
                                                ToolTip.delay: 500
                                                onClicked: collection.removeMesh(index)
                                            }

                                            Label {
                                                Layout.fillWidth: true
                                                text: label && label.length > 0 ? label : root.randomLabel(index, "Mesh")
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
                                    }
                            }

                            Label {
                                anchors.centerIn: parent
                                visible: root.collection && root.collection.meshModel.count === 0
                                text: "No mesh entries"
                                color: palette.mid
                            }
                        }
                    }
                }

                ExpandableGroup {
                    id: sfmDataGroup
                    Layout.fillWidth: true
                    expanded: true
                    title: "SFM DATA (" + (root.collection ? root.collection.sfmDataModel.count : 0) + ")"

                    ColumnLayout {
                        width: parent.width
                        spacing: 2

                        ListView {
                            id: sfmDataListView
                            visible: sfmDataGroup.expanded
                            Layout.fillWidth: true
                            Layout.preferredHeight: Math.min(contentHeight, 220)
                            clip: true
                            spacing: 4

                            ScrollBar.vertical: MScrollBar { id: sfmDataScrollBar }

                            model: root.collection ? root.collection.sfmDataModel : null

                            delegate: MouseArea {
                                    id: sfmDataDelegate
                                    hoverEnabled: true
                                    property bool rowVisible: root.layerVisible("sfmData", index)
                                    property bool rowPickable: root.layerPicking("sfmData", index)
                                    property bool rowExpanded: false
                                    property real rowMaxResectionId: root.sfmDataMaxResectionId(index, 100)

                                    onRowVisibleChanged: {
                                        root.setLayerVisible("sfmData", index, rowVisible)
                                    }
                                    onRowPickableChanged: {
                                        root.setLayerPicking("sfmData", index, rowPickable)
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

                                            MaterialToolButton {
                                                text: MaterialIcons.clear
                                                font.pointSize: 10
                                                ToolTip.text: "Remove"
                                                ToolTip.delay: 500
                                                onClicked: collection.removeSfmData(index)
                                            }

                                            Label {
                                                Layout.fillWidth: true
                                                text: label && label.length > 0 ? label : root.randomLabel(index, "SfmData")
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
                                                value: root.layerCameraSize("sfmData", index, 1.0)
                                                onMoved: root.setLayerCameraSize("sfmData", index, value)
                                                ToolTip.text: "Camera Scale: " + value.toFixed(2)
                                                ToolTip.visible: hovered || pressed
                                                ToolTip.delay: 100
                                            }

                                            Label {
                                                text: root.layerCameraSize("sfmData", index, 1.0).toFixed(2)
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
                                                value: root.layerPointSize("sfmData", index, 1.0)
                                                onValueChanged: root.setLayerPointSize("sfmData", index, value)
                                                ToolTip.text: "Point Size: " + value.toFixed(2)
                                                ToolTip.visible: hovered || pressed
                                                ToolTip.delay: 100
                                            }

                                            Label {
                                                text: root.layerPointSize("sfmData", index, 1.0).toFixed(2)
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
                                visible: root.collection && root.collection.sfmDataModel.count === 0
                                text: "No sfmData entries"
                                color: palette.mid
                            }
                        }
                    }
                }

                Item {
                    Layout.fillHeight: true
                }

                Label {
                    visible: !root.collection
                    text: "Waiting for Viewer3D collection..."
                    color: palette.mid
                    horizontalAlignment: Text.AlignHCenter
                    Layout.fillWidth: true
                }
            }
        }
    }
}
